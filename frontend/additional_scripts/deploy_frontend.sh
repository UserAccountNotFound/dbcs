#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# Конфигурация
# ==============================================================================
APP_NAME="dbcs"
FRONTEND_DIR="/opt/${APP_NAME}/frontend"
WEB_ROOT="/var/www/${APP_NAME}/frontend"
NGINX_CONF="/etc/nginx/sites-available/${APP_NAME}"
NGINX_LINK="/etc/nginx/sites-enabled/${APP_NAME}"
NGINX_MAIN_CONF="/etc/nginx/nginx.conf"

# Настройки бэкенда (для проксирования API в Nginx)
APP_PORT="8000"
API_PREFIX="/api"
BACKEND_ENV="/opt/${APP_NAME}/backend/.env"
TLS_STATE_FILE="/opt/${APP_NAME}/.tls.env"
SSL_MODE="${SSL_MODE:-}"
SSL_CERT_PATH="${SSL_CERT_PATH:-}"
SSL_KEY_PATH="${SSL_KEY_PATH:-}"
SERVER_NAME="${SERVER_NAME:-}"
ACME_WEBROOT="${ACME_WEBROOT:-/var/www/letsencrypt}"
SSL_DIR="${SSL_DIR:-/etc/nginx/ssl/${APP_NAME}}"
PUBLIC_BASE_URL="${PUBLIC_BASE_URL:-}"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ==============================================================================
# Вспомогательные функции
# ==============================================================================
log_info()  { echo -e "${GREEN}[INFO_(frontend)]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN_(frontend)]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR_(frontend)]${NC} $1"; }

# При curl|bash stdin = скрипт; читаем с /dev/tty. EOF → default (set -e не валит).
# read_from_tty VAR "prompt" "default" [--silent]
read_from_tty() {
    local __var="$1"
    local __prompt="$2"
    local __default="${3:-}"
    local __silent=0
    local __reply=""
    shift 3 || true
    [[ "${1:-}" == "--silent" ]] && __silent=1

    if [[ -n "${DBCS_NONINTERACTIVE:-}" ]]; then
        __reply="${__default}"
        printf -v "${__var}" '%s' "${__reply}"
        return 0
    fi

    if [[ -r /dev/tty ]]; then
        if [[ "${__silent}" -eq 1 ]]; then
            IFS= read -r -s -p "${__prompt}" __reply </dev/tty || true
            echo "" >/dev/tty 2>/dev/null || echo ""
        else
            IFS= read -r -p "${__prompt}" __reply </dev/tty || true
        fi
    elif [[ -t 0 ]]; then
        if [[ "${__silent}" -eq 1 ]]; then
            IFS= read -r -s -p "${__prompt}" __reply || true
            echo ""
        else
            IFS= read -r -p "${__prompt}" __reply || true
        fi
    else
        log_warn "Нет TTY — используем значение по умолчанию."
        __reply="${__default}"
    fi

    if [[ -z "${__reply}" ]]; then
        __reply="${__default}"
    fi
    printf -v "${__var}" '%s' "${__reply}"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "Этот скрипт должен быть запущен от имени root (или через sudo)."
        exit 1
    fi
}

# ==============================================================================
# 1. Установка Node.js (если отсутствует)
# ==============================================================================
install_node() {
    if command -v node &> /dev/null; then
        log_info "Node.js уже установлен: $(node -v)"
        return 0
    fi

    log_info "Установка Node.js 20.x LTS..."
    
    # Временно сбрасываем локали
    export LANG=C
    export LC_ALL=C
    
    apt-get update -qq
    apt-get install -y -qq curl ca-certificates

    # nodesource setup читает свой stdin из pipe — не трогаем /dev/tty здесь
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    DEBIAN_FRONTEND=noninteractive apt-get install -y -qq nodejs
    
    log_info "Node.js успешно установлен: $(node -v)"
}

# ==============================================================================
# 2. Подготовка PWA иконок (защита от падения vite-plugin-pwa)
# ==============================================================================
prepare_pwa_assets() {
    log_info "Проверка PWA иконок в папке public/..."
    cd "$FRONTEND_DIR"
    
    mkdir -p public
    
    # vite-plugin-pwa требует наличия иконок, указанных в vite.config.ts.
    # Если их нет, создаем минимальные валидные PNG 1x1 (прозрачные), чтобы сборка не упала.
    # !!! НЕЗАБЫТЬ заменить их на реальные дизайн-макеты.
    if [[ ! -f "public/pwa-192x192.png" ]]; then
        echo "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=" | base64 -d > public/pwa-192x192.png
    fi
    if [[ ! -f "public/pwa-512x512.png" ]]; then
        echo "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=" | base64 -d > public/pwa-512x512.png
    fi
    if [[ ! -f "public/favicon.ico" ]]; then
        touch public/favicon.ico
    fi
    
    log_info "PWA ассеты проверены/созданы."
}

# ==============================================================================
# 3. Сборка Frontend (Vite)
# ==============================================================================
build_frontend() {
    log_info "Подготовка к сборке Frontend..."
    cd "$FRONTEND_DIR"

    # Создаем .env.production для Vite. 
    # В production API находится на том же домене, поэтому используем относительный путь.
    cat <<EOF > .env.production
VITE_API_BASE_URL=/api/v1
VITE_APP_TITLE=Digital Bussines Cards Service
EOF

    log_info "Установка зависимостей..."
    # npm ci быстрее и надежнее, если есть package-lock.json. Иначе fallback на install.
    if [[ -f "package-lock.json" ]]; then
        npm ci --silent
    else
        npm install --silent
    fi

    log_info "Сборка production-версии (npm run build)..."
    npm run build

    if [[ ! -d "dist" ]]; then
        log_error "Сборка прошла, но папка dist не найдена!"
        exit 1
    fi
    
    log_info "Сборка успешно завершена."
}

# ==============================================================================
# 4. Деплой статики в WEB_ROOT
# ==============================================================================
deploy_static() {
    log_info "Копирование собранных файлов в ${WEB_ROOT}..."
    
    mkdir -p "${WEB_ROOT}"
    
    # Очищаем старую версию (важно: ? защищает от удаления корня, если переменная пуста)
    rm -rf "${WEB_ROOT:?}/"*
    
    # Копируем новую сборку
    cp -r "${FRONTEND_DIR}/dist/"* "${WEB_ROOT}/"

    # Метка версии для install.sh / мониторинга
    if [[ -f "${FRONTEND_DIR}/package.json" ]]; then
        python3 -c "import json; print(json.load(open('${FRONTEND_DIR}/package.json'))['version'])" \
            > "${WEB_ROOT}/VERSION"
    fi

    # Устанавливаем владельца (www-data для Nginx) и права
    chown -R www-data:www-data "${WEB_ROOT}"
    chmod -R 755 "${WEB_ROOT}"
    
    log_info "Статика успешно развернута."
}

# ==============================================================================
# 5. Настройка Nginx (Объединяем API Proxy и Frontend Static)

# =============================================================================
# TLS: состояние от deploy_backend.sh (без повторного вопроса)
# =============================================================================

load_tls_state() {
    if [[ -f "${TLS_STATE_FILE}" ]]; then
        set -a
        # shellcheck disable=SC1090
        source "${TLS_STATE_FILE}"
        set +a
        log_info "TLS-состояние загружено из ${TLS_STATE_FILE} (mode=${SSL_MODE:-?})"
    fi

    if [[ -z "${PUBLIC_BASE_URL}" && -f "${BACKEND_ENV}" ]]; then
        PUBLIC_BASE_URL="$(grep -E '^PUBLIC_BASE_URL=' "${BACKEND_ENV}" | head -n1 | cut -d= -f2- | tr -d '"' | tr -d "'")"
    fi

    if [[ -z "${SERVER_NAME}" && -n "${PUBLIC_BASE_URL}" ]]; then
        SERVER_NAME="$(python3 -c 'from urllib.parse import urlparse; import sys; print(urlparse(sys.argv[1]).hostname or "")' "${PUBLIC_BASE_URL}" 2>/dev/null || true)"
    fi
    if [[ -z "${SERVER_NAME}" ]]; then
        SERVER_NAME="$(hostname -f 2>/dev/null || hostname || echo _)"
    fi

    if [[ -z "${SSL_CERT_PATH}" || -z "${SSL_KEY_PATH}" || ! -f "${SSL_CERT_PATH:-/n}" || ! -f "${SSL_KEY_PATH:-/n}" ]]; then
        local host="${SERVER_NAME}"
        if [[ -f "/etc/letsencrypt/live/${host}/fullchain.pem" && -f "/etc/letsencrypt/live/${host}/privkey.pem" ]]; then
            SSL_CERT_PATH="/etc/letsencrypt/live/${host}/fullchain.pem"
            SSL_KEY_PATH="/etc/letsencrypt/live/${host}/privkey.pem"
            SSL_MODE="${SSL_MODE:-existing}"
        elif [[ -f "${SSL_DIR}/${host}.crt" && -f "${SSL_DIR}/${host}.key" ]]; then
            SSL_CERT_PATH="${SSL_DIR}/${host}.crt"
            SSL_KEY_PATH="${SSL_DIR}/${host}.key"
            SSL_MODE="${SSL_MODE:-existing}"
        elif [[ -f "/etc/nginx/ssl/${host}.crt" && -f "/etc/nginx/ssl/${host}.key" ]]; then
            SSL_CERT_PATH="/etc/nginx/ssl/${host}.crt"
            SSL_KEY_PATH="/etc/nginx/ssl/${host}.key"
            SSL_MODE="${SSL_MODE:-existing}"
        fi
    fi

    # proxy = TLS на внешнем reverse proxy → локально слушаем HTTP
    if [[ "${SSL_MODE}" == "proxy" ]]; then
        log_info "SSL_MODE=proxy — локальный nginx на HTTP, публичный URL https."
        SSL_MODE="http"
    fi

    if [[ -z "${SSL_MODE}" ]]; then
        if [[ "${PUBLIC_BASE_URL}" == https://* && -n "${SSL_CERT_PATH}" && -f "${SSL_CERT_PATH}" ]]; then
            SSL_MODE="existing"
        else
            SSL_MODE="http"
        fi
    fi

    if [[ "${SSL_MODE}" != "http" ]]; then
        if [[ -z "${SSL_CERT_PATH}" || -z "${SSL_KEY_PATH}" || ! -f "${SSL_CERT_PATH}" || ! -f "${SSL_KEY_PATH}" ]]; then
            log_warn "SSL_MODE=${SSL_MODE}, но сертификаты не найдены — откат на HTTP (PWA недоступно)."
            SSL_MODE="http"
        fi
    fi
}

nginx_ensure_rate_limits() {
    # Имена зон совпадают с deploy_backend.sh
    if ! grep -q "limit_req_zone.*auth_limit" "$NGINX_MAIN_CONF"; then
        log_info "Добавление зоны Rate Limiting: auth_limit..."
        sed -i '/http {/a \    limit_req_zone $binary_remote_addr zone=auth_limit:10m rate=5r/m;' "$NGINX_MAIN_CONF"
    fi
    if ! grep -q "limit_req_zone.*public_limit" "$NGINX_MAIN_CONF"; then
        log_info "Добавление зоны Rate Limiting: public_limit..."
        sed -i '/http {/a \    limit_req_zone $binary_remote_addr zone=public_limit:10m rate=30r/m;' "$NGINX_MAIN_CONF"
    fi
    if ! grep -q "limit_req_zone.*uploads_limit" "$NGINX_MAIN_CONF"; then
        log_info "Добавление зоны Rate Limiting: uploads_limit..."
        sed -i '/http {/a \    limit_req_zone $binary_remote_addr zone=uploads_limit:10m rate=10r/m;' "$NGINX_MAIN_CONF"
    fi
}

nginx_site_locations() {
    cat <<EOF
    root ${WEB_ROOT};
    index index.html;
    client_max_body_size 10M;

    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self'; connect-src 'self'; manifest-src 'self';" always;

    location ${API_PREFIX}/v1/auth/ {
        limit_req zone=auth_limit burst=10 nodelay;
        limit_req_status 429;
        proxy_pass http://127.0.0.1:${APP_PORT};
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location ${API_PREFIX}/v1/files/ {
        limit_req zone=uploads_limit burst=5 nodelay;
        limit_req_status 429;
        proxy_pass http://127.0.0.1:${APP_PORT};
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 90s;
        proxy_send_timeout 90s;
        proxy_read_timeout 90s;
    }

    location ${API_PREFIX}/v1/public/ {
        limit_req zone=public_limit burst=20 nodelay;
        limit_req_status 429;
        proxy_pass http://127.0.0.1:${APP_PORT};
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location ^~ ${API_PREFIX}/v1/admin/settings/backup {
        proxy_pass http://127.0.0.1:${APP_PORT};
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;
    }

    location ${API_PREFIX}/ {
        proxy_pass http://127.0.0.1:${APP_PORT};
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    location = /sw.js {
        add_header Cache-Control "no-cache, no-store, must-revalidate";
        try_files \$uri =404;
    }
    location = /manifest.webmanifest {
        add_header Cache-Control "no-cache, no-store, must-revalidate";
        try_files \$uri =404;
    }

    location /assets/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        try_files \$uri =404;
    }

    location / {
        try_files \$uri \$uri/ /index.html;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
    }

    location ~ /\\. {
        deny all;
        access_log off;
        log_not_found off;
    }
EOF
}

# ==============================================================================
# 5. Настройка Nginx (статика + API + TLS из backend)
# ==============================================================================
setup_nginx() {
    log_info "Настройка Nginx для PWA + API (с учётом TLS)..."
    load_tls_state
    nginx_ensure_rate_limits

    local server_name="${SERVER_NAME:-_}"
    local locations
    locations="$(nginx_site_locations)"

    if [[ "${SSL_MODE}" == "http" ]]; then
        log_warn "HTTP без TLS — PWA (service worker) будет недоступно."
        cat > "${NGINX_CONF}" <<EOF
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name ${server_name};

${locations}
}
EOF
    else
        log_info "HTTPS (${SSL_MODE}): ${SSL_CERT_PATH}"
        mkdir -p "${ACME_WEBROOT}/.well-known/acme-challenge"
        cat > "${NGINX_CONF}" <<EOF
# HTTP → HTTPS (+ ACME)
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name ${server_name};

    location ^~ /.well-known/acme-challenge/ {
        root ${ACME_WEBROOT};
        default_type text/plain;
    }

    location / {
        return 301 https://\$host\$request_uri;
    }
}

server {
    listen 443 ssl;
    listen [::]:443 ssl;
    http2 on;
    server_name ${server_name};

    ssl_certificate     ${SSL_CERT_PATH};
    ssl_certificate_key ${SSL_KEY_PATH};
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:10m;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers off;

    add_header Strict-Transport-Security "max-age=31536000" always;

${locations}
}
EOF
    fi

    ln -sf "${NGINX_CONF}" "${NGINX_LINK}"
    rm -f /etc/nginx/sites-enabled/default

    nginx -t
    systemctl reload nginx

    if [[ "${SSL_MODE}" == "http" ]]; then
        log_info "Nginx: HTTP. Откройте http://${server_name}/login"
    else
        log_info "Nginx: HTTPS. Откройте https://${server_name}/login"
    fi
}

# ==============================================================================
# Главный сценарий выполнения
# ==============================================================================
main() {
    log_info "=== Начало развертывания DBCS Frontend ==="

    # apt/dpkg не должны ждать ввода при установке из curl|bash
    export DEBIAN_FRONTEND=noninteractive

    check_root
    install_node
    prepare_pwa_assets
    build_frontend
    deploy_static
    setup_nginx
    
    log_info "=== Развертывание Frontend завершено ==="
    if [[ "${SSL_MODE}" == "http" ]]; then
        log_info "Откройте http://<host>/login (без HTTPS PWA недоступно)"
    else
        log_info "Откройте https://<host>/login"
    fi
}

main "$@"
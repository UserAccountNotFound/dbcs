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
# ==============================================================================
setup_nginx() {
    log_info "Настройка Nginx для раздачи PWA и проксирования API..."
    
    # Убеждаемся, что зоны Rate Limiting существуют
    if ! grep -q "limit_req_zone.*auth_limit" "$NGINX_MAIN_CONF"; then
        log_info "Добавление зон Rate Limiting в глобальный nginx.conf..."
        sed -i '/http {/a \    limit_req_zone $binary_remote_addr zone=auth_limit:10m rate=5r/m;\n    limit_req_zone $binary_remote_addr zone=public_limit:10m rate=30r/m;' "$NGINX_MAIN_CONF"
    fi
    
    # Генерируем финальный конфиг сайта
    cat <<EOF > "$NGINX_CONF"
server {
    listen 80;
    server_name _; # Замените на ваш домен или IP

    # Корень для фронтенда
    root ${WEB_ROOT};
    index index.html;

    client_max_body_size 10M;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;
    
    # CSP для PWA (разрешаем same-origin, inline стили для Tailwind, blob/data для QR и vCard)
    add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self'; connect-src 'self'; manifest-src 'self';" always;

    # 1. Rate Limiting & API Proxy (Бэкенд)
    location ${API_PREFIX}/v1/auth/ {
        limit_req zone=auth_limit burst=10 nodelay;
        limit_req_status 429;
        proxy_pass http://127.0.0.1:${APP_PORT};
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
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

    # 2. PWA Service Worker и Manifest (СТРОГО без кэширования)
    location = /sw.js {
        add_header Cache-Control "no-cache, no-store, must-revalidate";
        try_files \$uri =404;
    }
    location = /manifest.webmanifest {
        add_header Cache-Control "no-cache, no-store, must-revalidate";
        try_files \$uri =404;
    }

    # 3. Static Assets (Vite hashes) - Агрессивное кэширование на год
    location /assets/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        try_files \$uri =404;
    }

    # 4. Fallback для Vue Router (History Mode) и index.html
    location / {
        try_files \$uri \$uri/ /index.html;
        # index.html не должен кэшироваться, чтобы пользователь всегда получал свежую версию PWA
        add_header Cache-Control "no-cache, no-store, must-revalidate";
    }

    # Запрет доступа к скрытым файлам
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }
}
EOF

    ln -sf "$NGINX_CONF" "$NGINX_LINK"
    rm -f /etc/nginx/sites-enabled/default

    nginx -t
    systemctl reload nginx
    
    log_info "Nginx настроен и перезагружен."
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
    log_info "Откройте браузер и перейдите по адресу вашего сервера (например, http://<IP>/login)"
}

main "$@"
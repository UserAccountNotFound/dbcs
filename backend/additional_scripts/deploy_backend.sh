#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# Конфигурация
# ==============================================================================
APP_NAME="dbcs"
APP_USER="ecard"
BACKEND_DIR="/opt/${APP_NAME}/backend"
LOG_DIR="/var/log/${APP_NAME}"
UPLOADS_DIR="/var/lib/${APP_NAME}/uploads"  # директория для загруженных файлов
BACKUPS_DIR="/var/lib/${APP_NAME}/backups"
BACKUPS_DIR_ALT="/opt/${APP_NAME}/backups"
ENV_FILE="${BACKEND_DIR}/.env"
ENV_EXAMPLE="${BACKEND_DIR}/.env.example"
SYSTEMD_SERVICE="/etc/systemd/system/${APP_NAME}-backend.service"
SYSTEMD_BACKUP_SERVICE="/etc/systemd/system/${APP_NAME}-backup.service"
SYSTEMD_BACKUP_TIMER="/etc/systemd/system/${APP_NAME}-backup.timer"
NGINX_CONF="/etc/nginx/sites-available/${APP_NAME}"
NGINX_LINK="/etc/nginx/sites-enabled/${APP_NAME}"

# Настройки БД
DB_HOST="127.0.0.1"
DB_PORT="3306"
DB_NAME="e_cards"
DB_USER="ecard_user"
# Пароль: DB_PASSWORD из окружения, иначе из существующего .env, иначе генерация.
DB_PASSWORD="${DB_PASSWORD:-}" 

# Настройки приложения
APP_PORT="8000"
# PUBLIC_BASE_URL будет определен ниже автоматически или введен пользователем
API_PREFIX="/api"
MAX_UPLOAD_SIZE_MB=5  # НОВОЕ: максимальный размер загружаемого файла

# TLS: http | selfsigned | letsencrypt | existing | proxy
# SSL_MODE из окружения пропускает интерактивный вопрос.
# proxy = HTTP на этом хосте, HTTPS на внешнем reverse proxy (PUBLIC_BASE_URL=https://...)
SSL_MODE="${SSL_MODE:-}"
SSL_CERT_PATH=""
SSL_KEY_PATH=""
SSL_DIR="/etc/nginx/ssl/${APP_NAME}"
ACME_WEBROOT="/var/www/letsencrypt"
SERVER_NAME=""
LETSENCRYPT_EMAIL="${LETSENCRYPT_EMAIL:-}"
TLS_STATE_FILE="/opt/${APP_NAME}/.tls.env"
FRONTEND_WEB_ROOT="/var/www/${APP_NAME}/frontend"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ==============================================================================
# Вспомогательные функции
# ==============================================================================
log_info()  { echo -e "${GREEN}[INFO_(backend)]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN_(backend)]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR_(backend)]${NC} $1"; }

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

generate_secret() {
    #python3 -c 'import secrets; print(secrets.token_hex(32))'
    python3 -c 'import secrets; print(secrets.token_urlsafe(64))' # более секурно
}

resolve_db_password() {
    if [[ -n "$DB_PASSWORD" ]]; then
        return 0
    fi

    if [[ -f "$ENV_FILE" ]]; then
        local extracted
        extracted="$(
            ENV_FILE="$ENV_FILE" python3 - <<'PY'
import os
from pathlib import Path
from urllib.parse import unquote, urlparse

env_path = Path(os.environ["ENV_FILE"])
for line in env_path.read_text(encoding="utf-8").splitlines():
    if line.startswith("DATABASE_URL="):
        url = line.split("=", 1)[1].strip().strip('"').strip("'")
        parsed = urlparse(url)
        if parsed.password:
            print(unquote(parsed.password))
        break
PY
        )"
        if [[ -n "$extracted" ]]; then
            DB_PASSWORD="$extracted"
            log_info "DB_PASSWORD взят из существующего DATABASE_URL в .env."
            return 0
        fi
    fi

    DB_PASSWORD="$(openssl rand -hex 16)"
    log_warn "DB_PASSWORD не задан — сгенерирован случайный пароль (будет записан в DATABASE_URL в .env)."
}


# =============================================================================
# TLS / hostname / PUBLIC_BASE_URL
# =============================================================================

extract_url_host() {
    python3 -c 'from urllib.parse import urlparse; import sys; print(urlparse(sys.argv[1]).hostname or "")' "$1"
}

is_ip_host() {
    local h="$1"
    [[ "$h" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]] && return 0
    [[ "$h" == *:* ]] && return 0
    return 1
}

detect_server_host() {
    local fqdn=""
    if command -v hostname &>/dev/null; then
        fqdn=$(hostname -f 2>/dev/null || echo "")
    fi
    if [[ -z "$fqdn" || "$fqdn" == "localhost"* || "$fqdn" == "(none)" ]]; then
        local ip_addr=""
        if command -v hostname &>/dev/null; then
            ip_addr=$(hostname -I 2>/dev/null | awk '{print $1}')
        fi
        if [[ -n "$ip_addr" && ! "$ip_addr" =~ ^127\. ]]; then
            if command -v host &>/dev/null; then
                fqdn=$(host "$ip_addr" 2>/dev/null | grep -oP 'name pointer \K.*' || echo "")
            elif command -v dig &>/dev/null; then
                fqdn=$(dig -x "$ip_addr" +short 2>/dev/null | grep -v '^$' | tail -1 | sed 's/\.$//' || echo "")
            fi
            if [[ -z "$fqdn" ]]; then
                fqdn="$ip_addr"
            fi
        fi
    fi
    if [[ -z "$fqdn" || "$fqdn" == "localhost"* || "$fqdn" == "(none)" ]]; then
        fqdn=$(hostname 2>/dev/null || echo "localhost")
    fi
    echo "$(echo "$fqdn" | xargs)"
}

find_existing_certs() {
    local host="$1"
    SSL_CERT_PATH=""
    SSL_KEY_PATH=""
    if [[ -f "/etc/letsencrypt/live/${host}/fullchain.pem" && -f "/etc/letsencrypt/live/${host}/privkey.pem" ]]; then
        SSL_CERT_PATH="/etc/letsencrypt/live/${host}/fullchain.pem"
        SSL_KEY_PATH="/etc/letsencrypt/live/${host}/privkey.pem"
        return 0
    fi
    if [[ -f "${SSL_DIR}/${host}.crt" && -f "${SSL_DIR}/${host}.key" ]]; then
        SSL_CERT_PATH="${SSL_DIR}/${host}.crt"
        SSL_KEY_PATH="${SSL_DIR}/${host}.key"
        return 0
    fi
    if [[ -f "/etc/nginx/ssl/${host}.crt" && -f "/etc/nginx/ssl/${host}.key" ]]; then
        SSL_CERT_PATH="/etc/nginx/ssl/${host}.crt"
        SSL_KEY_PATH="/etc/nginx/ssl/${host}.key"
        return 0
    fi
    return 1
}

generate_self_signed_cert() {
    local host="$1"
    local san
    mkdir -p "${SSL_DIR}"
    SSL_CERT_PATH="${SSL_DIR}/${host}.crt"
    SSL_KEY_PATH="${SSL_DIR}/${host}.key"
    if is_ip_host "${host}"; then
        san="IP:${host}"
    else
        san="DNS:${host},DNS:localhost,IP:127.0.0.1"
    fi
    log_info "Генерация самоподписанного сертификата для ${host}..."
    if ! openssl req -x509 -nodes -newkey rsa:2048 -days 825 \
        -keyout "${SSL_KEY_PATH}" -out "${SSL_CERT_PATH}" \
        -subj "/CN=${host}/O=DBCS/C=RU" \
        -addext "subjectAltName=${san}" 2>/dev/null; then
        openssl req -x509 -nodes -newkey rsa:2048 -days 825 \
            -keyout "${SSL_KEY_PATH}" -out "${SSL_CERT_PATH}" \
            -subj "/CN=${host}/O=DBCS/C=RU"
    fi
    chmod 640 "${SSL_KEY_PATH}" || true
    chmod 644 "${SSL_CERT_PATH}" || true
    log_info "Сертификат: ${SSL_CERT_PATH}"
}

obtain_letsencrypt_cert() {
    local host="$1"
    local email="${LETSENCRYPT_EMAIL:-}"
    if is_ip_host "${host}" || [[ "${host}" == "localhost" || "${host}" == *".local" ]]; then
        log_error "Let's Encrypt недоступен для IP / localhost."
        return 1
    fi
    if [[ -z "${email}" ]]; then
        read_from_tty email "Email для Let's Encrypt: " ""
    fi
    if [[ -z "${email}" || "${email}" != *@* ]]; then
        log_error "Нужен корректный email для Let's Encrypt."
        return 1
    fi
    LETSENCRYPT_EMAIL="${email}"
    log_info "Установка certbot..."
    DEBIAN_FRONTEND=noninteractive apt-get install -y -qq certbot >/dev/null
    mkdir -p "${ACME_WEBROOT}/.well-known/acme-challenge"
    cat > "${NGINX_CONF}" <<EOF
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name ${host};
    location ^~ /.well-known/acme-challenge/ {
        root ${ACME_WEBROOT};
        default_type text/plain;
    }
    location / { return 200 'DBCS ACME\n'; add_header Content-Type text/plain; }
}
EOF
    ln -sf "${NGINX_CONF}" "${NGINX_LINK}"
    rm -f /etc/nginx/sites-enabled/default
    nginx -t && systemctl reload nginx
    if ! certbot certonly --webroot -w "${ACME_WEBROOT}" -d "${host}" \
        --email "${email}" --agree-tos --non-interactive --keep-until-expiring; then
        log_error "certbot не получил сертификат."
        return 1
    fi
    SSL_CERT_PATH="/etc/letsencrypt/live/${host}/fullchain.pem"
    SSL_KEY_PATH="/etc/letsencrypt/live/${host}/privkey.pem"
    log_info "Let's Encrypt сертификат получен."
}

write_tls_state() {
    mkdir -p "$(dirname "${TLS_STATE_FILE}")"
    cat > "${TLS_STATE_FILE}" <<EOF
# Сгенерировано deploy_backend.sh — читает deploy_frontend.sh
SSL_MODE=${SSL_MODE}
SSL_CERT_PATH=${SSL_CERT_PATH}
SSL_KEY_PATH=${SSL_KEY_PATH}
SERVER_NAME=${SERVER_NAME}
PUBLIC_BASE_URL=${PUBLIC_BASE_URL}
ACME_WEBROOT=${ACME_WEBROOT}
SSL_DIR=${SSL_DIR}
EOF
    chmod 644 "${TLS_STATE_FILE}"
    log_info "TLS-состояние: ${TLS_STATE_FILE} (mode=${SSL_MODE})"
}

tls_scheme_for_mode() {
    case "${SSL_MODE}" in
        http) echo "http" ;;
        proxy) echo "https" ;;  # снаружи HTTPS
        *) echo "https" ;;
    esac
}

build_public_url() {
    local scheme host
    scheme="$(tls_scheme_for_mode)"
    host="${1:-${SERVER_NAME}}"
    echo "${scheme}://${host}"
}

configure_server_host() {
    log_info "Определение имени сервера..."
    if [[ -n "${PUBLIC_BASE_URL:-}" ]]; then
        SERVER_NAME="$(extract_url_host "${PUBLIC_BASE_URL}")"
        if [[ -z "${SERVER_NAME}" ]]; then
            log_error "Не удалось извлечь hostname из PUBLIC_BASE_URL=${PUBLIC_BASE_URL}"
            exit 1
        fi
        log_info "Имя сервера из PUBLIC_BASE_URL: ${SERVER_NAME}"
        return 0
    fi
    local detected answer
    detected="$(detect_server_host)"
    SERVER_NAME="${detected}"
    echo
    echo "=============================================================================="
    echo " Имя сервера (hostname / FQDN)"
    echo "=============================================================================="
    echo " Обнаружено: ${detected}"
    echo " (схема http/https — после выбора TLS)"
    echo "=============================================================================="
    read_from_tty answer "Использовать это имя? [Y/n] или введите своё: " "Y"
    if [[ -z "$answer" || "$answer" =~ ^[Yy]$ ]]; then
        SERVER_NAME="${detected}"
    elif [[ "$answer" =~ ^[Nn]$ ]]; then
        read_from_tty SERVER_NAME "Введите hostname или FQDN: " "${detected}"
        SERVER_NAME="$(echo "${SERVER_NAME}" | xargs)"
    else
        answer="${answer#http://}"; answer="${answer#https://}"; answer="${answer%%/*}"
        SERVER_NAME="$(echo "${answer}" | xargs)"
    fi
    if [[ -z "${SERVER_NAME}" ]]; then
        log_error "Имя сервера не может быть пустым."
        exit 1
    fi
    log_info "Имя сервера: ${SERVER_NAME}"
}

configure_tls() {
    if [[ -z "${SERVER_NAME}" ]]; then
        log_error "SERVER_NAME не задан."
        exit 1
    fi
    if find_existing_certs "${SERVER_NAME}"; then
        SSL_MODE="existing"
        log_info "Найдены SSL-сертификаты для ${SERVER_NAME}."
        return 0
    fi
    local choice="${SSL_MODE}"
    if [[ -z "${choice}" ]]; then
        echo
        echo "=============================================================================="
        echo " SSL / HTTPS (нужен для PWA; за reverse proxy — вариант 4)"
        echo "=============================================================================="
        echo " Сертификаты для «${SERVER_NAME}» не найдены."
        echo
        echo "  [1] HTTP только — без TLS на этом хосте (PWA недоступно)"
        echo "  [2] Самоподписанный сертификат (по умолчанию)"
        echo "  [3] Let's Encrypt (нужен публичный DNS)"
        echo "  [4] За reverse proxy — HTTP здесь, HTTPS снаружи"
        echo "=============================================================================="
        read_from_tty choice "Выберите [1/2/3/4] (Enter = 2): " "2"
    fi
    case "${choice}" in
        1|http|HTTP)
            SSL_MODE="http"
            SSL_CERT_PATH=""; SSL_KEY_PATH=""
            log_warn "HTTP без TLS. PWA недоступно."
            ;;
        3|letsencrypt|le|LE)
            SSL_MODE="letsencrypt"
            log_info "Let's Encrypt — сертификат при настройке Nginx (frontend)."
            # Отложим certbot до nginx с ACME; сгенерируем selfsigned временно только если нужно
            ;;
        4|proxy|PROXY)
            SSL_MODE="proxy"
            SSL_CERT_PATH=""; SSL_KEY_PATH=""
            log_info "Режим reverse proxy: локально HTTP, PUBLIC_BASE_URL будет https://"
            ;;
        2|selfsigned|self|"")
            SSL_MODE="selfsigned"
            generate_self_signed_cert "${SERVER_NAME}"
            log_warn "Самоподписанный сертификат — браузер покажет предупреждение."
            ;;
        *)
            log_warn "Неизвестный SSL_MODE=${choice} — selfsigned."
            SSL_MODE="selfsigned"
            generate_self_signed_cert "${SERVER_NAME}"
            ;;
    esac
    log_info "TLS: mode=${SSL_MODE}, host=${SERVER_NAME}"
}

configure_public_base_url() {
    local scheme default_url user_input
    scheme="$(tls_scheme_for_mode)"
    default_url="$(build_public_url "${SERVER_NAME}")"

    if [[ -n "${PUBLIC_BASE_URL:-}" ]]; then
        PUBLIC_BASE_URL="${PUBLIC_BASE_URL%/}"
        if [[ ! "$PUBLIC_BASE_URL" =~ ^https?:// ]]; then
            PUBLIC_BASE_URL="${scheme}://${PUBLIC_BASE_URL}"
        fi
        # Для локального TLS/HTTP схема должна совпадать с mode (кроме proxy — оставляем https снаружи)
        if [[ "${SSL_MODE}" != "proxy" ]]; then
            PUBLIC_BASE_URL="$(build_public_url "$(extract_url_host "${PUBLIC_BASE_URL}")")"
        else
            # proxy: принудительно https публичный URL
            PUBLIC_BASE_URL="https://$(extract_url_host "${PUBLIC_BASE_URL}")"
        fi
        log_info "PUBLIC_BASE_URL: ${PUBLIC_BASE_URL}"
        write_tls_state
        return 0
    fi

    echo
    echo "=============================================================================="
    echo " Настройка PUBLIC_BASE_URL"
    echo "=============================================================================="
    echo " TLS: ${SSL_MODE} → схема ${scheme}"
    echo " Предлагаемый URL: ${default_url}"
    echo "=============================================================================="
    read_from_tty user_input "Использовать предложенный URL? [Y/n] или введите свой: " "Y"
    if [[ -z "$user_input" || "$user_input" =~ ^[Yy]$ ]]; then
        PUBLIC_BASE_URL="${default_url}"
    elif [[ "$user_input" =~ ^[Nn]$ ]]; then
        local raw=""
        while true; do
            read_from_tty raw "Hostname или полный URL: " ""
            [[ -z "$raw" ]] && { log_error "Не может быть пустым."; continue; }
            if [[ "$raw" =~ ^https?:// ]]; then
                PUBLIC_BASE_URL="$(build_public_url "$(extract_url_host "$raw")")"
            else
                raw="${raw#http://}"; raw="${raw#https://}"; raw="${raw%%/*}"
                PUBLIC_BASE_URL="$(build_public_url "$raw")"
            fi
            break
        done
    else
        if [[ "$user_input" =~ ^https?:// ]]; then
            PUBLIC_BASE_URL="$(build_public_url "$(extract_url_host "$user_input")")"
        else
            user_input="${user_input#http://}"; user_input="${user_input#https://}"; user_input="${user_input%%/*}"
            PUBLIC_BASE_URL="$(build_public_url "$user_input")"
        fi
    fi
    # proxy: всегда https снаружи
    if [[ "${SSL_MODE}" == "proxy" ]]; then
        PUBLIC_BASE_URL="https://$(extract_url_host "${PUBLIC_BASE_URL}")"
    fi
    log_info "PUBLIC_BASE_URL: ${PUBLIC_BASE_URL}"
    write_tls_state
}



# ==============================================================================
# 1. Установка системных зависимостей и регенерация локалей
# ==============================================================================
install_dependencies() {
    log_info "Обновление списка пакетов и установка зависимостей..."
    
    # Временно сбрасываем локали в "C", чтобы подавить варнинги perl при работе apt
    export LANG=C
    export LC_ALL=C
    
    apt-get update -qq
    
    # libmagic1 нужен для python-magic (валидация MIME-типов загружаемых файлов)
    apt-get install -y -qq sudo locales python3 python3-venv python3-pip libmagic1 mariadb-server mariadb-client nginx curl rsync openssl
    
    log_info "Настройка системных локалей..."
    
    # 1. Раскомментируем нужные локали в /etc/locale.gen (если они там есть с #)
    sed -i -e 's/^# *\(en_US.UTF-8 UTF-8\)/\1/' /etc/locale.gen
    sed -i -e 's/^# *\(ru_RU.UTF-8 UTF-8\)/\1/' /etc/locale.gen
    
    # 2. Генерируем локали на основе раскомментированных строк
    locale-gen
    
    # 3. Устанавливаем локаль по умолчанию в системе
    update-locale LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8
    
    # 4. Экспортируем валидные локали в текущий сеанс bash, 
    # чтобы оставшиеся шаги скрипта не выдавали perl warnings
    export LANG=en_US.UTF-8
    export LC_ALL=en_US.UTF-8
    
    log_info "Системные зависимости и локали успешно настроены."
}

# ==============================================================================
# 2. Создание системного пользователя и директорий
# ==============================================================================
setup_user_and_dirs() {
    log_info "Настройка системного пользователя и директорий..."
    
    if ! id -u "$APP_USER" >/dev/null 2>&1; then
        useradd --system --no-create-home --shell /usr/sbin/nologin "$APP_USER"
        log_info "Пользователь $APP_USER создан."
    else
        log_info "Пользователь $APP_USER уже существует."
    fi

    mkdir -p "$BACKEND_DIR"
    mkdir -p "$LOG_DIR"
    
    # НОВОЕ: Создаем директорию для загружаемых файлов вне webroot
    # Это важно для безопасности: файлы не должны быть доступны через Nginx напрямую
    mkdir -p "$UPLOADS_DIR"
    mkdir -p "$BACKUPS_DIR"
    # Альтернативный путь из UI; должен существовать до systemd ReadWritePaths
    mkdir -p "$BACKUPS_DIR_ALT"
    
#    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
#    if [[ "$SCRIPT_DIR" != "$BACKEND_DIR" ]]; then
#        log_info "Копирование файлов проекта в $BACKEND_DIR..."
#        # Исключаем виртуальное окружение, кэш и локальные секреты
#        rsync -a --exclude='.venv' --exclude='__pycache__' --exclude='.env' --exclude='.git' "$SCRIPT_DIR/" "$BACKEND_DIR/"
#    fi

    chown -R "$APP_USER":"$APP_USER" "$BACKEND_DIR"
    chown -R "$APP_USER":"$APP_USER" "$LOG_DIR"
    
    # НОВОЕ: Выставляем права на директорию загрузок
    # 700 - только владелец может читать/писать (защита от других системных пользователей)
    chown -R "$APP_USER":"$APP_USER" "$UPLOADS_DIR"
    chmod 700 "$UPLOADS_DIR"
    log_info "Директория загрузок $UPLOADS_DIR создана и защищена."

    chown -R "$APP_USER":"$APP_USER" "$BACKUPS_DIR"
    chmod 700 "$BACKUPS_DIR"
    chown -R "$APP_USER":"$APP_USER" "$BACKUPS_DIR_ALT"
    chmod 700 "$BACKUPS_DIR_ALT"
    log_info "Директории бэкапов $BACKUPS_DIR и $BACKUPS_DIR_ALT созданы и защищены."
}

# ==============================================================================
# 3. Настройка .env файла (Безопасная замена через Python)
# ==============================================================================
setup_env() {
    log_info "Проверка файла окружения (.env)..."
    
    if [[ ! -f "$ENV_FILE" ]]; then
        log_warn "Файл $ENV_FILE не найден. Создаем базовый из шаблона."
        
        if [[ -f "$ENV_EXAMPLE" ]]; then
            cp "$ENV_EXAMPLE" "$ENV_FILE"
        else
            cat <<EOF > "$ENV_FILE"
APP_NAME="DBCS Service API"
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=
DATABASE_URL=
ALLOWED_ORIGINS=${PUBLIC_BASE_URL}
PUBLIC_BASE_URL=${PUBLIC_BASE_URL}
API_V1_PREFIX=${API_PREFIX}/v1
DOCS_ENABLED=false
REDOC_ENABLED=true
DB_ECHO=false
ACCESS_TOKEN_TTL_MINUTES=15
REFRESH_TOKEN_TTL_DAYS=7
SELF_REGISTRATION_ENABLED=false
REFRESH_COOKIE_NAME=refresh_token
REFRESH_COOKIE_SECURE=false
REFRESH_COOKIE_SAMESITE=lax
UPLOADS_DIR=${UPLOADS_DIR}
MAX_UPLOAD_SIZE_MB=${MAX_UPLOAD_SIZE_MB}
EOF
        fi
    fi
    
    # Генерируем секреты и подставляем URL базы через Python, 
    # чтобы избежать проблем со спецсимволами в паролях (sed ломается от |, &, /)
    log_info "Обновление секретов и DATABASE_URL в .env..."
    
    NEW_SECRET=$(generate_secret)
    # URL-encode пароля для DATABASE_URL
    DB_PASSWORD_ENC="$(P="${DB_PASSWORD}" python3 -c 'import os,urllib.parse; print(urllib.parse.quote(os.environ["P"], safe=""))')"
    DB_URL="mysql+pymysql://${DB_USER}:${DB_PASSWORD_ENC}@${DB_HOST}:${DB_PORT}/${DB_NAME}?charset=utf8mb4"

    COOKIE_SECURE=false
    if [[ "${PUBLIC_BASE_URL}" == https://* ]]; then
        COOKIE_SECURE=true
    fi
    export ENV_FILE DB_URL NEW_SECRET PUBLIC_BASE_URL UPLOADS_DIR MAX_UPLOAD_SIZE_MB COOKIE_SECURE
    
    python3 -c '
import os
env_file = os.environ["ENV_FILE"]
db_url = os.environ["DB_URL"]
new_secret = os.environ["NEW_SECRET"]
public_url = os.environ["PUBLIC_BASE_URL"]
uploads_dir = os.environ["UPLOADS_DIR"]
max_upload_mb = os.environ["MAX_UPLOAD_SIZE_MB"]
cookie_secure = os.environ.get("COOKIE_SECURE", "true")

with open(env_file, "r") as f:
    lines = f.readlines()

with open(env_file, "w") as f:
    for line in lines:
        if line.startswith("DATABASE_URL="):
            f.write(f"DATABASE_URL={db_url}\n")
        elif line.startswith("SECRET_KEY=") and ("change-me" in line or line.strip() == "SECRET_KEY="):
            f.write(f"SECRET_KEY={new_secret}\n")
        elif line.startswith("PUBLIC_BASE_URL="):
            f.write(f"PUBLIC_BASE_URL={public_url}\n")
        elif line.startswith("ALLOWED_ORIGINS="):
            f.write(f"ALLOWED_ORIGINS={public_url}\n")
        elif line.startswith("UPLOADS_DIR="):
            f.write(f"UPLOADS_DIR={uploads_dir}\n")
        elif line.startswith("MAX_UPLOAD_SIZE_MB="):
            f.write(f"MAX_UPLOAD_SIZE_MB={max_upload_mb}\n")
        elif line.startswith("REFRESH_COOKIE_SECURE="):
            f.write(f"REFRESH_COOKIE_SECURE={cookie_secure}\n")
        else:
            f.write(line)
    # Если DATABASE_URL не было в файле, добавляем в конец
    if not any(line.startswith("DATABASE_URL=") for line in lines):
        f.write(f"\nDATABASE_URL={db_url}\n")

    # Гарантируем наличие новых переменных для Auth/Cookies и загрузки файлов, если их нет
    required_vars = {
        "SELF_REGISTRATION_ENABLED": "false",
        "REFRESH_COOKIE_NAME": "refresh_token",
        "REFRESH_COOKIE_SECURE": cookie_secure,
        "REFRESH_COOKIE_SAMESITE": "lax",
        "API_V1_PREFIX": "/api/v1",
        "UPLOADS_DIR": uploads_dir,
        "MAX_UPLOAD_SIZE_MB": max_upload_mb
    }
    with open(env_file, "r") as f:
        current_lines = f.readlines()
        
    with open(env_file, "a") as f:
        for var, val in required_vars.items():
            if not any(l.startswith(f"{var}=") for l in current_lines):
                f.write(f"\n{var}={val}\n")
'

    chmod 600 "$ENV_FILE"
    chown "$APP_USER":"$APP_USER" "$ENV_FILE"
    log_info "Файл .env создан/обновлен и защищен (права 600)."
}

# ==============================================================================
# 4. Настройка базы данных MariaDB
# ==============================================================================
setup_database() {
    log_info "Проверка подключения к базе данных..."

    # Никогда не ждём пароль в TTY: явный --password= (в т.ч. пустой) + timeout.
    run_mysql_root() {
        local pwd="${DB_ROOT_PASSWORD-}"
        if command -v timeout >/dev/null 2>&1; then
            MYSQL_PWD="$pwd" timeout 15 mariadb -u root --password="$pwd" --batch --connect-timeout=5 "$@"
        else
            MYSQL_PWD="$pwd" mariadb -u root --password="$pwd" --batch --connect-timeout=5 "$@"
        fi
    }

    ensure_mysql_root() {
        if run_mysql_root -e "SELECT 1;" &>/dev/null; then
            return 0
        fi

        if [[ -n "${DBCS_NONINTERACTIVE:-}" ]]; then
            log_error "Нет доступа MariaDB root (нужен для грантов). Задайте DB_ROOT_PASSWORD или запустите интерактивно."
            exit 1
        fi

        log_info "Нужен пароль root MariaDB (Enter — пустой; символы скрыты):"
        DB_ROOT_PASSWORD=""
        read_from_tty DB_ROOT_PASSWORD "MariaDB root password: " "" --silent
        if ! run_mysql_root -e "SELECT 1;" &>/dev/null; then
            log_error "Не удалось подключиться к MariaDB как root."
            exit 1
        fi
    }

    app_user_has_drop() {
        MYSQL_PWD="$DB_PASSWORD" mariadb -u "$DB_USER" -h "$DB_HOST" --batch -N \
            -e "SHOW GRANTS FOR CURRENT_USER();" 2>/dev/null | grep -q "DROP"
    }

    # Права для миграций + полного restore из mysqldump (DROP/routines).
    DB_APP_GRANTS="SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, ALTER, INDEX, REFERENCES, CREATE VIEW, SHOW VIEW, CREATE ROUTINE, ALTER ROUTINE, EXECUTE, EVENT, TRIGGER, LOCK TABLES"

    apply_db_grants() {
        local recreate_user="${1:-0}"
        export DB_NAME DB_USER DB_PASSWORD DB_APP_GRANTS
        export DBCS_RECREATE_USER="$recreate_user"
        SQL="$(python3 - <<'PY'
import os
def esc(s: str) -> str:
    return s.replace("\\", "\\\\").replace("'", "''")
db = os.environ["DB_NAME"]
user = os.environ["DB_USER"]
pwd = esc(os.environ["DB_PASSWORD"])
grants = os.environ["DB_APP_GRANTS"]
recreate = os.environ.get("DBCS_RECREATE_USER", "0") == "1"
lines = [
    f"CREATE DATABASE IF NOT EXISTS `{db}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;",
]
if recreate:
    lines.extend([
        f"CREATE USER IF NOT EXISTS '{user}'@'localhost' IDENTIFIED BY '{pwd}';",
        f"CREATE USER IF NOT EXISTS '{user}'@'127.0.0.1' IDENTIFIED BY '{pwd}';",
        f"ALTER USER '{user}'@'localhost' IDENTIFIED VIA mysql_native_password USING PASSWORD('{pwd}');",
        f"ALTER USER '{user}'@'127.0.0.1' IDENTIFIED VIA mysql_native_password USING PASSWORD('{pwd}');",
    ])
lines.extend([
    f"GRANT {grants} ON `{db}`.* TO '{user}'@'localhost';",
    f"GRANT {grants} ON `{db}`.* TO '{user}'@'127.0.0.1';",
    "FLUSH PRIVILEGES;",
])
print("\n".join(lines))
PY
)"
        if ! printf '%s\n' "$SQL" | run_mysql_root; then
            log_error "Не удалось применить права БД."
            exit 1
        fi
    }

    if MYSQL_PWD="$DB_PASSWORD" mariadb -u "$DB_USER" -h "$DB_HOST" -e "USE $DB_NAME; SELECT 1;" &>/dev/null; then
        if app_user_has_drop; then
            log_info "База данных доступна, права приложения уже достаточны (есть DROP)."
            return 0
        fi
        log_info "База данных доступна — дополняем права приложения (нужен DROP для restore)."
        ensure_mysql_root
        apply_db_grants 0
        log_info "Права пользователя $DB_USER обновлены."
        return 0
    fi

    log_warn "Не удалось подключиться к БД — создаём базу и пользователя."
    ensure_mysql_root
    log_info "Создание базы данных и пользователя..."
    apply_db_grants 1
    log_info "База данных и пользователь успешно созданы."
}

setup_python() {
    log_info "Настройка виртуального окружения Python..."
    
    cd "$BACKEND_DIR"
    
    if [[ ! -d ".venv" ]]; then
        sudo -u "$APP_USER" python3 -m venv .venv
        log_info "Виртуальное окружение создано."
    fi

    log_info "Установка зависимостей Python..."
    sudo -u "$APP_USER" .venv/bin/pip install --upgrade pip wheel -qq
    
    if [[ -f "requirements.txt" ]]; then
        sudo -u "$APP_USER" .venv/bin/pip install -r requirements.txt -qq
    fi
    
    sudo -u "$APP_USER" .venv/bin/pip install gunicorn -qq

    # Только upgrade из репозитория — без autogenerate на сервере
    if [[ ! -f "alembic.ini" ]]; then
        log_error "Файл alembic.ini не найден в $BACKEND_DIR!"
        exit 1
    fi
    if [[ ! -d "alembic/versions" ]] || ! find alembic/versions/ -type f -name "*.py" 2>/dev/null | grep -q .; then
        log_error "Нет миграций в alembic/versions/. Добавьте их в репозиторий."
        exit 1
    fi

    log_info "Применение миграций базы данных (Alembic upgrade head)..."
    sudo -u "$APP_USER" bash -c "set -a; source .env; set +a; .venv/bin/alembic upgrade head"
    log_info "Миграции успешно применены."
}

# ==============================================================================
# 6. Настройка Systemd сервиса
# ==============================================================================
setup_systemd() {
    log_info "Создание systemd сервиса..."
    
    # НОВОЕ: добавляем UPLOADS_DIR в ReadWritePaths, 
    # иначе сервис не сможет писать загруженные файлы из-за ProtectSystem=strict
    cat <<EOF > "$SYSTEMD_SERVICE"
[Unit]
Description=DBCS Backend API (FastAPI + Gunicorn)
After=network.target mariadb.service

[Service]
Type=notify
User=${APP_USER}
Group=${APP_USER}
WorkingDirectory=${BACKEND_DIR}
EnvironmentFile=${ENV_FILE}

# Запуск через Gunicorn с Uvicorn workers для асинхронности
ExecStart=${BACKEND_DIR}/.venv/bin/gunicorn app.main:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --workers 4 \
    --bind 127.0.0.1:${APP_PORT} \
    --access-logfile ${LOG_DIR}/access.log \
    --error-logfile ${LOG_DIR}/error.log \
    --worker-tmp-dir /dev/shm

Restart=always
RestartSec=5
KillMode=mixed
TimeoutStopSec=10

# Security hardening
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
PrivateTmp=true
ReadWritePaths=${BACKEND_DIR} ${LOG_DIR} /var/lib/${APP_NAME} ${BACKUPS_DIR_ALT}

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable "${APP_NAME}-backend.service"
    systemctl restart "${APP_NAME}-backend.service"
    
    log_info "Systemd сервис запущен и добавлен в автозагрузку."
}

# ==============================================================================
# 6b. Таймер резервного копирования
# ==============================================================================
setup_backup_timer() {
    log_info "Настройка systemd timer для резервного копирования..."

    cat <<EOF > "$SYSTEMD_BACKUP_SERVICE"
[Unit]
Description=DBCS scheduled backup
After=network.target mariadb.service ${APP_NAME}-backend.service

[Service]
Type=oneshot
User=${APP_USER}
Group=${APP_USER}
WorkingDirectory=${BACKEND_DIR}
EnvironmentFile=${ENV_FILE}
Environment=PYTHONPATH=${BACKEND_DIR}
ExecStart=${BACKEND_DIR}/.venv/bin/python ${BACKEND_DIR}/additional_scripts/run_backup.py --if-due
Nice=10
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
PrivateTmp=true
ReadWritePaths=${BACKEND_DIR} ${LOG_DIR} /var/lib/${APP_NAME} ${BACKUPS_DIR_ALT}
EOF

    cat <<EOF > "$SYSTEMD_BACKUP_TIMER"
[Unit]
Description=DBCS backup schedule (hourly check)

[Timer]
OnCalendar=hourly
Persistent=true
RandomizedDelaySec=5m

[Install]
WantedBy=timers.target
EOF

    systemctl daemon-reload
    systemctl enable --now "${APP_NAME}-backup.timer"
    log_info "Таймер ${APP_NAME}-backup.timer включён."
}

# ==============================================================================
# 7. Настройка Nginx
# ==============================================================================

setup_nginx() {
    log_info "Настройка Nginx (backend)..."

    # Rate-limit zones (идемпотентно)
    if ! grep -q "limit_req_zone.*auth_limit" /etc/nginx/nginx.conf; then
        sed -i '/http {/a \    limit_req_zone $binary_remote_addr zone=auth_limit:10m rate=5r/m;' /etc/nginx/nginx.conf
    fi
    if ! grep -q "limit_req_zone.*public_limit" /etc/nginx/nginx.conf; then
        sed -i '/http {/a \    limit_req_zone $binary_remote_addr zone=public_limit:10m rate=30r/m;' /etc/nginx/nginx.conf
    fi
    if ! grep -q "limit_req_zone.*uploads_limit" /etc/nginx/nginx.conf; then
        sed -i '/http {/a \    limit_req_zone $binary_remote_addr zone=uploads_limit:10m rate=10r/m;' /etc/nginx/nginx.conf
    fi

    local server_name="${SERVER_NAME:-_}"

    # Let's Encrypt до возможного early-return (нужен ACME на :80)
    if [[ "${SSL_MODE}" == "letsencrypt" ]]; then
        if ! find_existing_certs "${server_name}"; then
            if ! obtain_letsencrypt_cert "${server_name}"; then
                log_warn "Let's Encrypt не удался — откат на selfsigned."
                SSL_MODE="selfsigned"
                generate_self_signed_cert "${server_name}"
            fi
        fi
        write_tls_state
    fi

    # Не затираем полный vhost frontend (статика + TLS)
    if [[ -f "${NGINX_CONF}" ]] && grep -q "root ${FRONTEND_WEB_ROOT}" "${NGINX_CONF}" 2>/dev/null; then
        log_info "Найден nginx-конфиг frontend (${FRONTEND_WEB_ROOT}) — не перезаписываем."
        log_info "Финальный HTTPS/статика выставит deploy_frontend.sh."
        write_tls_state
        return 0
    fi

    # API-only HTTP stub — frontend перезапишет полный сайт
    cat > "${NGINX_CONF}" <<EOF
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name ${server_name};
    client_max_body_size 10M;

    location ^~ /.well-known/acme-challenge/ {
        root ${ACME_WEBROOT};
        default_type text/plain;
    }

    location ${API_PREFIX}/ {
        proxy_pass http://127.0.0.1:${APP_PORT};
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location / {
        return 200 'DBCS backend OK — deploy frontend for full site\n';
        add_header Content-Type text/plain;
    }
}
EOF
    mkdir -p "${ACME_WEBROOT}/.well-known/acme-challenge"
    ln -sf "${NGINX_CONF}" "${NGINX_LINK}"
    rm -f /etc/nginx/sites-enabled/default
    nginx -t
    systemctl restart nginx
    write_tls_state
    log_info "Временный HTTP nginx (API). Полный сайт — после deploy_frontend.sh."
}

verify_deployment() {
    log_info "Ожидание запуска приложения (5 секунд)..."
    sleep 5
    
    log_info "Проверка healthcheck..."
    if curl -s -f "http://127.0.0.1:${APP_PORT}${API_PREFIX}/v1/health" > /dev/null; then
        log_info "Backend успешно развернут и отвечает на запросы!"
        log_info "API доступен по адресу: http://127.0.0.1:${APP_PORT}${API_PREFIX}/v1"
        log_info "ReDoc документация: http://127.0.0.1:${APP_PORT}/api/redoc"
        log_info "Директория загрузок: ${UPLOADS_DIR}"
    else
        log_warn "Healthcheck не прошел. Проверь логи:"
        log_warn "journalctl -u ${APP_NAME}-backend.service -n 50"
        log_warn "cat ${LOG_DIR}/error.log"
    fi
}

# ==============================================================================
# Главный сценарий выполнения
# ==============================================================================
main() {
    log_info "=== Начало развертывания DBCS Backend ==="
    export DEBIAN_FRONTEND=noninteractive

    check_root
    install_dependencies
    setup_user_and_dirs
    # hostname → TLS → PUBLIC_BASE_URL; затем .env
    configure_server_host
    configure_tls
    configure_public_base_url
    resolve_db_password
    setup_env
    setup_database
    setup_python
    setup_systemd
    setup_backup_timer
    setup_nginx
    verify_deployment

    log_info "=== Развертывание завершено ==="
}

main "$@"
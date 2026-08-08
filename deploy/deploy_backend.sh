#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# Конфигурация
# ==============================================================================
APP_NAME="dbcs"
APP_USER="ecard"
BACKEND_DIR="/opt/${APP_NAME}/backend"
LOG_DIR="/var/log/${APP_NAME}"
UPLOADS_DIR="/var/lib/${APP_NAME}/uploads"  # НОВОЕ: директория для загруженных файлов
ENV_FILE="${BACKEND_DIR}/.env"
ENV_EXAMPLE="${BACKEND_DIR}/.env.example"
SYSTEMD_SERVICE="/etc/systemd/system/${APP_NAME}-backend.service"
NGINX_CONF="/etc/nginx/sites-available/${APP_NAME}"
NGINX_LINK="/etc/nginx/sites-enabled/${APP_NAME}"

# Настройки БД
DB_HOST="127.0.0.1"
DB_PORT="3306"
DB_NAME="e_cards"
DB_USER="ecard_user"
# ВНИМАНИЕ: Для продакшена используйте генератор (openssl rand -hex 16)
DB_PASSWORD="EcardM3GaPassW0rd" 

# Настройки приложения
APP_PORT="8000"
PUBLIC_BASE_URL="http://localhost"
API_PREFIX="/api"
MAX_UPLOAD_SIZE_MB=5  # НОВОЕ: максимальный размер загружаемого файла

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ==============================================================================
# Вспомогательные функции
# ==============================================================================
log_info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

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
    apt-get install -y -qq sudo locales python3 python3-venv python3-pip libmagic1 mariadb-server mariadb-client nginx curl rsync
    
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
REFRESH_COOKIE_SECURE=true
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
    DB_URL="mysql+pymysql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}?charset=utf8mb4"
    
    export ENV_FILE DB_URL NEW_SECRET PUBLIC_BASE_URL UPLOADS_DIR MAX_UPLOAD_SIZE_MB
    
    python3 -c '
import os
env_file = os.environ["ENV_FILE"]
db_url = os.environ["DB_URL"]
new_secret = os.environ["NEW_SECRET"]
public_url = os.environ["PUBLIC_BASE_URL"]
uploads_dir = os.environ["UPLOADS_DIR"]
max_upload_mb = os.environ["MAX_UPLOAD_SIZE_MB"]

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
        else:
            f.write(line)
    # Если DATABASE_URL не было в файле, добавляем в конец
    if not any(line.startswith("DATABASE_URL=") for line in lines):
        f.write(f"\nDATABASE_URL={db_url}\n")

    # Гарантируем наличие новых переменных для Auth/Cookies и загрузки файлов, если их нет
    required_vars = {
        "SELF_REGISTRATION_ENABLED": "false",
        "REFRESH_COOKIE_NAME": "refresh_token",
        "REFRESH_COOKIE_SECURE": "true",
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
    
    # Пытаемся подключиться под пользователем приложения
    if MYSQL_PWD="$DB_PASSWORD" mariadb -u "$DB_USER" -h "$DB_HOST" -e "USE $DB_NAME; SELECT 1;" &>/dev/null; then
        log_info "База данных и пользователь уже существуют и доступны."
        return 0
    fi

    log_warn "Не удалось подключиться к БД. Требуется создание базы и пользователя."
    log_info "Пожалуйста, введите пароль root для MariaDB (символы не будут отображаться):"
    
    set +e
    read -r -s DB_ROOT_PASSWORD
    echo ""
    set -e

    if [[ -z "$DB_ROOT_PASSWORD" ]]; then
        log_error "Пароль root не может быть пустым."
        exit 1
    fi

    log_info "Создание базы данных и пользователя..."
    
    set +x # Отключаем трассировку, чтобы пароль не попал в логи
    export MYSQL_PWD="$DB_ROOT_PASSWORD"
    mariadb -u root <<EOF
CREATE DATABASE IF NOT EXISTS \`${DB_NAME}\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS '${DB_USER}'@'localhost' IDENTIFIED BY '${DB_PASSWORD}';
CREATE USER IF NOT EXISTS '${DB_USER}'@'127.0.0.1' IDENTIFIED BY '${DB_PASSWORD}';

-- Принудительно используем mysql_native_password для совместимости с PyMySQL
ALTER USER '${DB_USER}'@'localhost' IDENTIFIED VIA mysql_native_password USING PASSWORD('${DB_PASSWORD}');
ALTER USER '${DB_USER}'@'127.0.0.1' IDENTIFIED VIA mysql_native_password USING PASSWORD('${DB_PASSWORD}');

GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, INDEX, REFERENCES, CREATE VIEW, SHOW VIEW, EVENT, TRIGGER, LOCK TABLES ON \`${DB_NAME}\`.* TO '${DB_USER}'@'localhost';
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, INDEX, REFERENCES, CREATE VIEW, SHOW VIEW, EVENT, TRIGGER, LOCK TABLES ON \`${DB_NAME}\`.* TO '${DB_USER}'@'127.0.0.1';

FLUSH PRIVILEGES;
EOF

    if [[ $? -ne 0 ]]; then
        log_error "Не удалось выполнить SQL команды. Проверьте пароль root MariaDB."
        exit 1
    fi
    unset MYSQL_PWD
    
    log_info "База данных и пользователь успешно созданы."
}

# ==============================================================================
# 5. Настройка Python окружения и миграций
# ==============================================================================
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

    # --- НАЧАЛО: Проверка структуры БД и генерация миграций ---
    log_info "Проверка структуры базы данных..."
    
    TABLE_COUNT=$(MYSQL_PWD="$DB_PASSWORD" mariadb -u "$DB_USER" -h "$DB_HOST" -D "$DB_NAME" -N -e "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = '${DB_NAME}';" 2>/dev/null || echo "0")

    # Проверяем наличие существующих миграций
    MIGRATIONS_EXIST=false
    if [[ -d "alembic/versions" ]] && find alembic/versions/ -type f -name "*.py" 2>/dev/null | grep -q .; then
        MIGRATIONS_EXIST=true
    fi

    if [[ "$TABLE_COUNT" == "0" ]]; then
        log_warn "База данных пуста (таблицы отсутствуют)."
        
        if [[ "$MIGRATIONS_EXIST" == true ]]; then
            # БД пуста, но миграции есть - применяем их
            log_info "Найдены существующие миграции. Применяем их для создания структуры..."
        else
            # БД пуста и миграций нет - генерируем
            if [[ -f "alembic.ini" ]]; then
                log_info "Миграции не найдены. Генерируем начальную миграцию..."
                sudo -u "$APP_USER" bash -c "set -a; source .env; set +a; .venv/bin/alembic revision --autogenerate -m 'initial schema'"
                
                if ! find alembic/versions/ -type f -name "*.py" | grep -q .; then
                    log_error "Миграция не сгенерирована (папка alembic/versions/ пуста)! Проверьте, что все SQLAlchemy модели импортируются в 'alembic/env.py'."
                    exit 1
                fi
            else
                log_error "Файл alembic.ini не найден в $BACKEND_DIR!"
                exit 1
            fi
        fi
    else
        log_info "Структура БД уже существует (найдено таблиц: $TABLE_COUNT)."
        
        # Проверяем, не отстает ли БД от миграций
        if [[ "$MIGRATIONS_EXIST" == true ]]; then
            log_info "Проверка актуальности структуры БД..."
            if ! sudo -u "$APP_USER" bash -c "set -a; source .env; set +a; .venv/bin/alembic check" &>/dev/null; then
                log_warn "Обнаружены непримененные изменения в моделях."
                log_info "Генерируем миграцию для синхронизации..."
                sudo -u "$APP_USER" bash -c "set -a; source .env; set +a; .venv/bin/alembic revision --autogenerate -m 'auto sync'"
            fi
        fi
    fi
    # --- КОНЕЦ: Проверка структуры БД ---

    log_info "Применение миграций базы данных (Alembic)..."
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
ReadWritePaths=${BACKEND_DIR} ${LOG_DIR} ${UPLOADS_DIR}

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable "${APP_NAME}-backend.service"
    systemctl restart "${APP_NAME}-backend.service"
    
    log_info "Systemd сервис запущен и добавлен в автозагрузку."
}

# ==============================================================================
# 7. Настройка Nginx
# ==============================================================================
setup_nginx() {
    log_info "Настройка Nginx..."
    
    # Проверяем и добавляем каждую зону rate limit отдельно
    # Это нужно, так как скрипт может запускаться многократно с разными версиями
    
    if ! grep -q "limit_req_zone.*auth_limit" /etc/nginx/nginx.conf; then
        log_info "Добавление зоны Rate Limiting: auth_limit..."
        sed -i '/http {/a \    limit_req_zone $binary_remote_addr zone=auth_limit:10m rate=5r/m;' /etc/nginx/nginx.conf
    fi
    
    if ! grep -q "limit_req_zone.*public_limit" /etc/nginx/nginx.conf; then
        log_info "Добавление зоны Rate Limiting: public_limit..."
        sed -i '/http {/a \    limit_req_zone $binary_remote_addr zone=public_limit:10m rate=30r/m;' /etc/nginx/nginx.conf
    fi
    
    if ! grep -q "limit_req_zone.*uploads_limit" /etc/nginx/nginx.conf; then
        log_info "Добавление зоны Rate Limiting: uploads_limit..."
        sed -i '/http {/a \    limit_req_zone $binary_remote_addr zone=uploads_limit:10m rate=10r/m;' /etc/nginx/nginx.conf
    fi
    
    cat <<EOF > "$NGINX_CONF"
server {
    listen 80;
    server_name _; # Замените на ваш домен или IP

    # Лимит на загрузку файлов (аватары, логотипы) - 10 Мегабайт
    # Должен быть чуть больше MAX_UPLOAD_SIZE_MB в приложении (5MB) с запасом на overhead
    client_max_body_size 10M;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;

    # Строгий лимит на Auth (защита от брутфорса)
    location ${API_PREFIX}/v1/auth/ {
        limit_req zone=auth_limit burst=10 nodelay;
        limit_req_status 429;
        
        proxy_pass http://127.0.0.1:${APP_PORT};
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # Строгий лимит на загрузку файлов (защита от DoS)
    location ${API_PREFIX}/v1/files/ {
        limit_req zone=uploads_limit burst=5 nodelay;
        limit_req_status 429;
        
        proxy_pass http://127.0.0.1:${APP_PORT};
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Увеличенный таймаут для загрузки больших файлов
        proxy_connect_timeout 90s;
        proxy_send_timeout 90s;
        proxy_read_timeout 90s;
    }

    # Умеренный лимит на публичные визитки (защита от парсинга/DDoS)
    location ${API_PREFIX}/v1/public/ {
        limit_req zone=public_limit burst=20 nodelay;
        limit_req_status 429;
        
        proxy_pass http://127.0.0.1:${APP_PORT};
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # Проксирование API на Gunicorn
    location ${API_PREFIX}/ {
        proxy_pass http://127.0.0.1:${APP_PORT};
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Timeout settings
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Блокируем прямой доступ к директории загрузок через Nginx (на всякий случай)
    location /uploads/ {
        deny all;
        return 404;
    }

    # Запрет доступа к скрытым файлам (например, .env, .git)
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
    systemctl restart nginx
    
    log_info "Nginx настроен и перезапущен."
}

# ==============================================================================
# 8. Финальная проверка
# ==============================================================================
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
    
    check_root
    install_dependencies
    setup_user_and_dirs
    setup_env
    setup_database
    setup_python
    setup_systemd
    setup_nginx
    verify_deployment
    
    log_info "=== Развертывание завершено ==="
}

main "$@"
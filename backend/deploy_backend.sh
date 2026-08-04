#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# Конфигурация
# ==============================================================================
APP_NAME="dbcs"
APP_USER="ecard"
BACKEND_DIR="/opt/${APP_NAME}/backend"
LOG_DIR="/var/log/${APP_NAME}"
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
DB_PASSWORD="EcardM3GaPassW0rd" # Заменить генератором паролей

# Настройки приложения
APP_PORT="8000"
PUBLIC_BASE_URL="http://localhost"
API_PREFIX="/api"

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
    # Генерирует криптографически стойкую случайную строку
    python3 -c 'import secrets; print(secrets.token_hex(32))'
}

# ==============================================================================
# 1. Установка системных зависимостей
# ==============================================================================
install_dependencies() {
    log_info "Обновление списка пакетов и установка зависимостей..."
    apt-get update -qq
    
    # sudo - для выполнения отдельных задач от имени администратора (root)
    # python3-venv - для виртуального окружения
    # mariadb-client - для проверки БД и выполнения SQL из скрипта
    # nginx - веб-сервер
    # curl - для healthcheck
    apt-get install -y -qq sudo python3 python3-venv python3-pip mariadb-client nginx curl > /dev/null
    log_info "Системные зависимости установлены."
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
    
    # Копируем исходный код в BACKEND_DIR, если мы запускаем скрипт из другой папки
    # (Предполагается, что скрипт лежит в корне исходников, которые нужно задеплоить)
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    if [[ "$SCRIPT_DIR" != "$BACKEND_DIR" ]]; then
        log_info "Копирование файлов проекта в $BACKEND_DIR..."
        rsync -a --exclude='.venv' --exclude='__pycache__' --exclude='.env' "$SCRIPT_DIR/" "$BACKEND_DIR/"
    fi

    chown -R "$APP_USER":"$APP_USER" "$BACKEND_DIR"
    chown -R "$APP_USER":"$APP_USER" "$LOG_DIR"
}

# ==============================================================================
# 3. Настройка .env файла
# ==============================================================================
setup_env() {
    log_info "Проверка файла окружения (.env)..."
    
    if [[ ! -f "$ENV_FILE" ]]; then
        log_warn "Файл $ENV_FILE не найден. Создаем из шаблона или генерируем базовый."
        
        if [[ -f "$ENV_EXAMPLE" ]]; then
            cp "$ENV_EXAMPLE" "$ENV_FILE"
        else
            # Создаем минимальный .env, если шаблона нет
            cat <<EOF > "$ENV_FILE"
APP_NAME="DBCS Service API"
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=
DATABASE_URL=mysql+pymysql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}?charset=utf8mb4
ALLOWED_ORIGINS=${PUBLIC_BASE_URL}
PUBLIC_BASE_URL=${PUBLIC_BASE_URL}
API_V1_PREFIX=${API_PREFIX}
DOCS_ENABLED=false
REDOC_ENABLED=true
DB_ECHO=false
ACCESS_TOKEN_TTL_MINUTES=15
REFRESH_TOKEN_TTL_DAYS=7
EOF
        fi
        
        # Генерируем SECRET_KEY, если он пустой или "change-me"
        if grep -q "^SECRET_KEY=$" "$ENV_FILE" || grep -q "change-me" "$ENV_FILE"; then
            log_info "Генерация нового SECRET_KEY..."
            NEW_SECRET=$(generate_secret)
            sed -i "s|^SECRET_KEY=.*|SECRET_KEY=${NEW_SECRET}|" "$ENV_FILE"
        fi
        
        # Обновляем DATABASE_URL на актуальный пароль
        sed -i "s|^DATABASE_URL=.*|DATABASE_URL=mysql+pymysql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}?charset=utf8mb4|" "$ENV_FILE"
        
        chmod 600 "$ENV_FILE"
        chown "$APP_USER":"$APP_USER" "$ENV_FILE"
        log_info "Файл .env создан и защищен (права 600)."
    else
        log_info "Файл .env уже существует. Пропускаем генерацию."
    fi
}

# ==============================================================================
# 4. Настройка базы данных MariaDB
# ==============================================================================
setup_database() {
    log_info "Проверка подключения к базе данных..."
    
    # Пытаемся подключиться под пользователем приложения
    if mariadb -u "$DB_USER" -p"$DB_PASSWORD" -h "$DB_HOST" -e "USE $DB_NAME; SELECT 1;" &>/dev/null; then
        log_info "База данных и пользователь уже существуют и доступны."
        return 0
    fi

    log_warn "Не удалось подключиться к БД. Требуется создание базы и пользователя."
    log_info "Пожалуйста, введите пароль root для MariaDB (символы не будут отображаться):"
    
    # Включаем echo для скрытия ввода, но сохраняем строгий режим
    set +e
    read -r -s DB_ROOT_PASSWORD
    echo ""
    set -e

    if [[ -z "$DB_ROOT_PASSWORD" ]]; then
        log_error "Пароль root не может быть пустым."
        exit 1
    fi

    log_info "Создание базы данных и пользователя..."
    
    # Выполняем SQL команды. Используем here-doc.
    # Обратите внимание: set +x отключает трассировку, чтобы пароль не попал в логи при отладке
    set +x
    mariadb -u root -p"$DB_ROOT_PASSWORD" <<EOF
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
    # Обновляем pip и устанавливаем зависимости от имени ecard
    sudo -u "$APP_USER" .venv/bin/pip install --upgrade pip wheel > /dev/null
    
    if [[ -f "requirements.txt" ]]; then
        sudo -u "$APP_USER" .venv/bin/pip install -r requirements.txt > /dev/null
    fi
    
    # Устанавливаем gunicorn для production
    sudo -u "$APP_USER" .venv/bin/pip install gunicorn > /dev/null

    log_info "Применение миграций базы данных (Alembic)..."
    # Запускаем alembic от имени ecard, передавая переменные окружения из .env
    sudo -u "$APP_USER" bash -c "set -a; source .env; set +a; .venv/bin/alembic upgrade head"
    
    log_info "Миграции успешно применены."
}

# ==============================================================================
# 6. Настройка Systemd сервиса
# ==============================================================================
setup_systemd() {
    log_info "Создание systemd сервиса..."
    
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
    --error-logfile ${LOG_DIR}/error.log

Restart=always
RestartSec=5
KillMode=mixed
TimeoutStopSec=10

# Security hardening
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=${BACKEND_DIR} ${LOG_DIR}

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
    
    # Создаем базовый конфиг для проксирования API
    cat <<EOF > "$NGINX_CONF"
server {
    listen 80;
    server_name _; # Замените на ваш домен или IP

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;

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

    # Запрет доступа к скрытым файлам (например, .env)
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }
}
EOF

    # Активируем конфиг
    ln -sf "$NGINX_CONF" "$NGINX_LINK"
    
    # Удаляем дефолтный сайт, если он мешает (опционально)
    rm -f /etc/nginx/sites-enabled/default

    # Проверяем конфиг и перезапускаем
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
    # Пытаемся сделать запрос к локальному API через Nginx или напрямую
    if curl -s -f "http://127.0.0.1:${APP_PORT}${API_PREFIX}/v1/health" > /dev/null; then
        log_info "Backend успешно развернут и отвечает на запросы!"
        log_info "API доступен по адресу: http://127.0.0.1:${APP_PORT}${API_PREFIX}/v1"
        log_info "ReDoc документация: http://127.0.0.1:${APP_PORT}/api/redoc"
    else
        log_warn "Healthcheck не прошел. Проверьте логи:"
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

# Запуск
main "$@"
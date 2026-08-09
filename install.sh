#!/usr/bin/env bash
set -euo pipefail


# Cценарий автоматизированного развертывания сервиса управления электронными визитками
# Digital Bussiness Card Service
#
#
# version 0.0.1

# папка установки
readonly INSTALL_DIR="/opt"
readonly DBCS_DIR="${INSTALL_DIR}/dbcs"
readonly REPO_URL="https://github.com/UserAccountNotFound/dbcs.git"
readonly EXPECTED_REPO_HASH="abc123..." # доверенный коммит (на будущее)

# Цвета для вывода
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly NC='\033[0m' # No Color

log_info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }


# Обработка прерываний
cleanup() {
    local exit_code=$?
    if [[ $exit_code -ne 0 ]]; then
        log_error "Развертывание прервано с кодом $exit_code."
        log_warn "Проверьте логи и повторите запуск."
    fi
}
trap cleanup EXIT

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "Этот скрипт должен быть запущен от имени root (или через sudo)."
        exit 1
    fi
}

check_os() {
    if [[ ! -f /etc/os-release ]]; then
        log_error "Не удалось определить операционную систему."
        exit 1
    fi

    # shellcheck source=/dev/null
    source /etc/os-release

    if [[ "${ID}" != "ubuntu" && "${ID}" != "debian" ]]; then
        log_error "Сейчас поддерживаются только Debian/Ubuntu. Текущая ОС: ${ID}"
        exit 1
    fi
    log_info "ОС определена: ${PRETTY_NAME}"
}

preinstall_system_pkg () {
    log_info "Обновление списка пакетов и предварительная установка системных зависимостей..."
    apt update -qq

    apt install -y -qq --no-install-recommends \
        git \
        curl
        
    log_info "Системные зависимости установлены."
}

clone_repository() {
    if [[ -d "${DBCS_DIR}/.git" ]]; then
        log_warn "Репозиторий уже клонирован. Обновляем..."
        cd "${DBCS_DIR}"
        git fetch origin
        git reset --hard origin/main
        cd - > /dev/null
    else
        log_info "Клонирование репозитория..."
        git clone --depth 1 "${REPO_URL}" "${DBCS_DIR}"
    fi

    cd "${DBCS_DIR}"
    local current_hash
    current_hash=$(git rev-parse HEAD)
    log_info "Текущий коммит: ${current_hash}"

    # проверка хеша
    # if [[ "${current_hash}" != "${EXPECTED_REPO_HASH}" ]]; then
    #     log_warn "Хеш коммита не совпадает с ожидаемым. Проверьте изменения."
    # fi

    cd - > /dev/null
}

# ============================================================================
# Развертывание backend
# ============================================================================

deploy_backend() {
    local backend_dir="${DBCS_DIR}/backend"

    if [[ ! -d "${backend_dir}" ]]; then
        log_error "Директория backend не найдена: ${backend_dir}"
        exit 1
    fi

    cd "${backend_dir}"
    chmod +x "./deploy_backend.sh"

    if [[ -x "./deploy_backend.sh" ]]; then
        log_info "Запуск deploy_backend.sh..."
        ./deploy_backend.sh
    else
        log_error "Сценарий развертывания бекенда не найден. Пропускаем шаг."
        return 0
    fi

    # Безопасная загрузка .env (только нужные переменные)
    if [[ -f .env ]]; then
        log_info "Загрузка конфигурации из .env..."
        export $(grep -v '^#' .env | grep '=' | xargs)
    else
        log_warn "Файл .env не найден. Убедитесь, что он будет создан."
    fi

    log_info "Инициализация базы данных..."
    .venv/bin/python create_SuperAdminUser.py
    .venv/bin/python seed_templates_vCard.py

    cd - > /dev/null
}

# ============================================================================
# Развертывание frontend
# ============================================================================

deploy_frontend() {
    local frontend_dir="${DBCS_DIR}/frontend"

    if [[ ! -d "${frontend_dir}" ]]; then
        log_error "Директория frontend не найдена: ${frontend_dir}"
        exit 1
    fi

    cd "${frontend_dir}"
    chmod +x "./deploy_frontend.sh"

    if [[ -x "./deploy_frontend.sh" ]]; then
        log_info "Запуск deploy_frontend.sh..."
        ./deploy_frontend.sh
    else
        log_error "Сценарий развертывания фронтенда не найден. Пропускаем шаг."
        return 0
    fi
}

# ==============================================================================
# Главный сценарий выполнения
# ==============================================================================

main() {
    log_info "=== Начало развертывания Digital Bussines Card Service ==="

    check_root
    check_os
    preinstall_system_pkg
    clone_repository
    deploy_backend
    deploy_frontend

    log_info "=== Развертывание завершено ==="
}

main "$@"
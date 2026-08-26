#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# Автоматизированное развёртывание Digital Business Card Service (DBCS)
#
# Использование:
#   sudo ./install.sh              # полная установка / обновление кода из git
#   sudo ./install.sh --check      # версии: main / dev / текущая (без изменений)
#   sudo ./install.sh --update     # проверить версии и обновить при необходимости
#   sudo ./install.sh check|update # то же самое
#
# version 1.0.0
# =============================================================================

readonly INSTALL_DIR="/opt"
readonly DBCS_DIR="${INSTALL_DIR}/dbcs"
readonly BACKEND_DIR="${DBCS_DIR}/backend"
readonly FRONTEND_DIR="${DBCS_DIR}/frontend"
readonly BACKEND_SCRIPTS_DIR="${BACKEND_DIR}/additional_scripts"
readonly FRONTEND_SCRIPTS_DIR="${FRONTEND_DIR}/additional_scripts"
readonly BACKEND_DEPLOY_SCRIPT="${BACKEND_SCRIPTS_DIR}/deploy_backend.sh"
readonly FRONTEND_DEPLOY_SCRIPT="${FRONTEND_SCRIPTS_DIR}/deploy_frontend.sh"
readonly FRONTEND_WEB_ROOT="/var/www/dbcs/frontend"
readonly BACKEND_SERVICE="dbcs-backend.service"
readonly HEALTH_URL="http://127.0.0.1:8000/api/v1/health"
readonly REPO_URL="https://github.com/UserAccountNotFound/dbcs.git"

readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

cleanup() {
    local exit_code=$?
    if [[ $exit_code -ne 0 ]]; then
        log_error "Сценарий завершился с кодом $exit_code."
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

preinstall_system_pkg() {
    log_info "Обновление списка пакетов и установка системных зависимостей..."
    apt update -qq
    apt install -y -qq --no-install-recommends git curl ca-certificates
    log_info "Системные зависимости установлены."
}

# Выбранная git-ветка (по умолчанию main)
GIT_BRANCH="main"

# Чтение с реального терминала (при curl|bash stdin = скрипт, не клавиатура).
# EOF / отсутствие TTY → значение по умолчанию; set -e не прерывает.
# read_from_tty VAR "prompt: " "default"
read_from_tty() {
    local __var="$1"
    local __prompt="$2"
    local __default="${3:-}"
    local __reply=""

    if [[ -n "${DBCS_NONINTERACTIVE:-}" ]]; then
        printf -v "${__var}" '%s' "${__default}"
        return 0
    fi

    if [[ -r /dev/tty ]]; then
        IFS= read -r -p "${__prompt}" __reply </dev/tty || true
    elif [[ -t 0 ]]; then
        IFS= read -r -p "${__prompt}" __reply || true
    else
        log_warn "Нет интерактивного TTY — «${__default}»"
        __reply="${__default}"
    fi

    if [[ -z "${__reply}" ]]; then
        __reply="${__default}"
    fi
    printf -v "${__var}" '%s' "${__reply}"
}

select_git_branch() {
    # Неинтерактивно: DBCS_BRANCH=main|dev
    local preset="${DBCS_BRANCH:-}"
    if [[ -n "${preset}" ]]; then
        preset="$(echo "${preset}" | tr '[:upper:]' '[:lower:]' | tr -d '[:space:]')"
        case "${preset}" in
            main|dev)
                GIT_BRANCH="${preset}"
                log_info "Ветка из DBCS_BRANCH: ${GIT_BRANCH}"
                return 0
                ;;
            *)
                log_warn "DBCS_BRANCH=${DBCS_BRANCH} неверна, спрашиваем интерактивно."
                ;;
        esac
    fi

    echo
    echo "──────────────────────────────────────────────"
    echo " Выбор ветки репозитория"
    echo "──────────────────────────────────────────────"
    echo "  [1] main  — стабильная (по умолчанию)"
    echo "  [2] dev   — разработка"
    echo "──────────────────────────────────────────────"

    local answer=""
    while true; do
        read_from_tty answer "С какой веткой работать? [main/dev] (Enter = main): " "main"
        answer="$(echo "${answer}" | tr '[:upper:]' '[:lower:]' | tr -d '[:space:]')"
        case "${answer}" in
            ""|1|main|m)
                GIT_BRANCH="main"
                break
                ;;
            2|dev|d)
                GIT_BRANCH="dev"
                break
                ;;
            *)
                log_warn "Введите main или dev."
                ;;
        esac
    done

    log_info "Выбрана ветка: ${GIT_BRANCH}"
}

clone_repository() {
    local branch="${GIT_BRANCH:-main}"

    if [[ -d "${DBCS_DIR}/.git" ]]; then
        log_warn "Репозиторий уже клонирован. Обновляем ветку «${branch}»..."
        git -C "${DBCS_DIR}" fetch origin --prune
        if ! git -C "${DBCS_DIR}" rev-parse --verify "origin/${branch}" >/dev/null 2>&1; then
            log_error "Ветка origin/${branch} не найдена на remote."
            exit 1
        fi
        git -C "${DBCS_DIR}" checkout -B "${branch}" "origin/${branch}"
        git -C "${DBCS_DIR}" reset --hard "origin/${branch}"
    else
        log_info "Клонирование репозитория (ветка ${branch})..."
        mkdir -p "${INSTALL_DIR}"
        git clone --depth 1 --branch "${branch}" "${REPO_URL}" "${DBCS_DIR}"
    fi

    log_info "Ветка: $(git -C "${DBCS_DIR}" rev-parse --abbrev-ref HEAD)"
    log_info "Коммит: $(git -C "${DBCS_DIR}" rev-parse HEAD)"
}

# -----------------------------------------------------------------------------
# Версии
# -----------------------------------------------------------------------------

# Извлечь app_version из текста config.py (stdin или файл).
parse_backend_version_text() {
    local ver=""
    ver="$(
        grep -E 'app_version[[:space:]]*:[[:space:]]*str[[:space:]]*=' \
            | head -n1 \
            | sed -E 's/.*app_version[[:space:]]*:[[:space:]]*str[[:space:]]*=[[:space:]]*"([^"]+)".*/\1/' \
            || true
    )"
    echo "${ver:-unknown}"
}

get_source_backend_version() {
    if [[ -f "${BACKEND_DIR}/app/core/config.py" ]]; then
        parse_backend_version_text < "${BACKEND_DIR}/app/core/config.py"
    else
        echo "unknown"
    fi
}

# Версия backend в git-ref (например origin/main), без checkout.
get_backend_version_at_ref() {
    local ref="${1:-}"
    local content=""
    if [[ -z "${ref}" ]] || [[ ! -d "${DBCS_DIR}/.git" ]]; then
        echo "unknown"
        return 0
    fi
    if ! git -C "${DBCS_DIR}" rev-parse --verify "${ref}" >/dev/null 2>&1; then
        echo "n/a"
        return 0
    fi
    content="$(git -C "${DBCS_DIR}" show "${ref}:backend/app/core/config.py" 2>/dev/null || true)"
    if [[ -z "${content}" ]]; then
        echo "unknown"
        return 0
    fi
    printf '%s\n' "${content}" | parse_backend_version_text
}

get_running_backend_version() {
    local ver=""
    if command -v curl >/dev/null 2>&1; then
        ver="$(
            curl -fsS --max-time 3 "${HEALTH_URL}" 2>/dev/null \
                | python3 -c 'import sys,json; print(json.load(sys.stdin).get("version",""))' 2>/dev/null \
                || true
        )"
    fi
    echo "${ver:-unknown}"
}

get_source_frontend_version() {
    if [[ -f "${FRONTEND_DIR}/package.json" ]]; then
        python3 -c "import json; print(json.load(open('${FRONTEND_DIR}/package.json'))['version'])" 2>/dev/null \
            || echo "unknown"
    else
        echo "unknown"
    fi
}

# Версия frontend в git-ref (например origin/dev), без checkout.
get_frontend_version_at_ref() {
    local ref="${1:-}"
    local content=""
    if [[ -z "${ref}" ]] || [[ ! -d "${DBCS_DIR}/.git" ]]; then
        echo "unknown"
        return 0
    fi
    if ! git -C "${DBCS_DIR}" rev-parse --verify "${ref}" >/dev/null 2>&1; then
        echo "n/a"
        return 0
    fi
    content="$(git -C "${DBCS_DIR}" show "${ref}:frontend/package.json" 2>/dev/null || true)"
    if [[ -z "${content}" ]]; then
        echo "unknown"
        return 0
    fi
    printf '%s\n' "${content}" | python3 -c 'import sys,json; print(json.load(sys.stdin).get("version","unknown"))' 2>/dev/null \
        || echo "unknown"
}

git_short_commit() {
    local ref="${1:-}"
    if [[ -z "${ref}" ]] || [[ ! -d "${DBCS_DIR}/.git" ]]; then
        echo "n/a"
        return 0
    fi
    git -C "${DBCS_DIR}" rev-parse --short "${ref}" 2>/dev/null || echo "n/a"
}

get_deployed_frontend_version() {
    if [[ -f "${FRONTEND_WEB_ROOT}/VERSION" ]]; then
        tr -d '[:space:]' < "${FRONTEND_WEB_ROOT}/VERSION"
        return 0
    fi
    echo "unknown"
}

# true если $1 < $2 (semver-подобно через sort -V)
version_lt() {
    local a="${1:-}"
    local b="${2:-}"
    [[ -z "$a" || "$a" == "unknown" ]] && return 0
    [[ -z "$b" || "$b" == "unknown" ]] && return 1
    [[ "$a" == "$b" ]] && return 1
    [[ "$(printf '%s\n' "$a" "$b" | sort -V | head -n1)" == "$a" ]]
}

print_versions() {
    local src_be run_be src_fe dep_fe
    src_be="$(get_source_backend_version)"
    run_be="$(get_running_backend_version)"
    src_fe="$(get_source_frontend_version)"
    dep_fe="$(get_deployed_frontend_version)"

    echo
    echo "──────────────────────────────────────────────"
    echo " Версии DBCS"
    echo "──────────────────────────────────────────────"
    echo "  Backend  (код / запущен):  ${src_be} / ${run_be}"
    echo "  Frontend (код / сайт):     ${src_fe} / ${dep_fe}"
    if systemctl is-active --quiet "${BACKEND_SERVICE}" 2>/dev/null; then
        echo "  Сервис ${BACKEND_SERVICE}: active"
    else
        echo "  Сервис ${BACKEND_SERVICE}: inactive/missing"
    fi
    echo "──────────────────────────────────────────────"
    echo
}

# --check: версии в origin/main, origin/dev и текущем рабочем дереве (+ runtime).
print_check_versions() {
    local local_branch="n/a"
    local local_commit="n/a"
    local be_main be_dev be_cur be_run
    local fe_main fe_dev fe_cur fe_dep
    local c_main c_dev

    if [[ -d "${DBCS_DIR}/.git" ]]; then
        log_info "Обновление сведений с origin (main, dev)..."
        if ! git -C "${DBCS_DIR}" fetch origin main dev --prune >/dev/null 2>&1; then
            # fallback: обычный fetch (shallow / частичные remotes)
            if ! git -C "${DBCS_DIR}" fetch origin --prune >/dev/null 2>&1; then
                log_warn "Не удалось выполнить git fetch (сеть/доступ) — показываем кэш remote."
            fi
        fi
        local_branch="$(git -C "${DBCS_DIR}" rev-parse --abbrev-ref HEAD 2>/dev/null || echo unknown)"
        local_commit="$(git_short_commit HEAD)"
    else
        log_warn "Репозиторий git не найден в ${DBCS_DIR} — remote-ветки недоступны."
    fi

    be_main="$(get_backend_version_at_ref origin/main)"
    be_dev="$(get_backend_version_at_ref origin/dev)"
    be_cur="$(get_source_backend_version)"
    be_run="$(get_running_backend_version)"

    fe_main="$(get_frontend_version_at_ref origin/main)"
    fe_dev="$(get_frontend_version_at_ref origin/dev)"
    fe_cur="$(get_source_frontend_version)"
    fe_dep="$(get_deployed_frontend_version)"

    c_main="$(git_short_commit origin/main)"
    c_dev="$(git_short_commit origin/dev)"

    echo
    echo "──────────────────────────────────────────────"
    echo " Версии DBCS (--check)"
    echo "──────────────────────────────────────────────"
    echo "  Текущая ветка:  ${local_branch} @ ${local_commit}"
    echo "  origin/main:    ${c_main}"
    echo "  origin/dev:     ${c_dev}"
    echo
    echo "  Backend:"
    echo "    origin/main:     ${be_main}"
    echo "    origin/dev:      ${be_dev}"
    echo "    текущий код:     ${be_cur}"
    echo "    запущено:        ${be_run}"
    echo
    echo "  Frontend:"
    echo "    origin/main:     ${fe_main}"
    echo "    origin/dev:      ${fe_dev}"
    echo "    текущий код:     ${fe_cur}"
    echo "    на сайте:        ${fe_dep}"
    if systemctl is-active --quiet "${BACKEND_SERVICE}" 2>/dev/null; then
        echo
        echo "  Сервис ${BACKEND_SERVICE}: active"
    else
        echo
        echo "  Сервис ${BACKEND_SERVICE}: inactive/missing"
    fi
    echo "──────────────────────────────────────────────"
    echo
}

# -----------------------------------------------------------------------------
# Обновление без полной переустановки
# -----------------------------------------------------------------------------

update_backend_inplace() {
    log_info "Обновление backend (зависимости, миграции, перезапуск)..."

    if [[ ! -d "${BACKEND_DIR}" ]]; then
        log_error "Каталог backend не найден: ${BACKEND_DIR}"
        return 1
    fi

    if [[ ! -x "${BACKEND_DIR}/.venv/bin/pip" ]]; then
        log_warn "venv не найден — запускаем полный deploy_backend.sh"
        deploy_backend
        return 0
    fi

    (
        cd "${BACKEND_DIR}"
        .venv/bin/pip install -q -r requirements.txt
        if [[ -f alembic.ini ]]; then
            .venv/bin/alembic upgrade head
        fi
    )

    if systemctl list-unit-files "${BACKEND_SERVICE}" >/dev/null 2>&1; then
        systemctl daemon-reload
        systemctl restart "${BACKEND_SERVICE}"
        sleep 1
        if systemctl is-active --quiet "${BACKEND_SERVICE}"; then
            log_info "Backend перезапущен: $(get_running_backend_version)"
        else
            log_error "Сервис ${BACKEND_SERVICE} не стал active после restart."
            systemctl --no-pager -l status "${BACKEND_SERVICE}" || true
            return 1
        fi
    else
        log_warn "systemd-юнит ${BACKEND_SERVICE} не найден — перезапуск пропущен."
    fi
}

update_frontend_inplace() {
    log_info "Обновление frontend (сборка и выкладка)..."
    deploy_frontend
    # страховка: VERSION должен появиться из deploy_frontend.sh
    if [[ ! -f "${FRONTEND_WEB_ROOT}/VERSION" ]]; then
        get_source_frontend_version > "${FRONTEND_WEB_ROOT}/VERSION" || true
    fi
    log_info "Frontend развёрнут: $(get_deployed_frontend_version)"
}

check_and_update_versions() {
    local force="${1:-0}"
    local src_be run_be src_fe dep_fe
    local need_be=0 need_fe=0

    print_versions

    src_be="$(get_source_backend_version)"
    run_be="$(get_running_backend_version)"
    src_fe="$(get_source_frontend_version)"
    dep_fe="$(get_deployed_frontend_version)"

    if [[ "${force}" == "1" ]]; then
        need_be=1
        need_fe=1
    else
        if ! systemctl is-active --quiet "${BACKEND_SERVICE}" 2>/dev/null; then
            log_warn "Backend-сервис не активен — требуется обновление/запуск."
            need_be=1
        elif version_lt "${run_be}" "${src_be}"; then
            log_warn "Backend устарел: запущено ${run_be}, в коде ${src_be}."
            need_be=1
        else
            log_info "Backend актуален (${run_be})."
        fi

        if version_lt "${dep_fe}" "${src_fe}"; then
            log_warn "Frontend устарел: на сайте ${dep_fe}, в коде ${src_fe}."
            need_fe=1
        else
            log_info "Frontend актуален (${dep_fe})."
        fi
    fi

    if [[ "${need_be}" -eq 0 && "${need_fe}" -eq 0 ]]; then
        log_info "Обновление не требуется."
        return 0
    fi

    if [[ "${need_be}" -eq 1 ]]; then
        update_backend_inplace
    fi
    if [[ "${need_fe}" -eq 1 ]]; then
        update_frontend_inplace
    fi

    print_versions
    log_info "Проверка/обновление версий завершены."
}

# -----------------------------------------------------------------------------
# Полный deploy
# -----------------------------------------------------------------------------

run_backend_python() {
    # Запуск python-скриптов из backend с загруженным .env
    (
        cd "${BACKEND_DIR}"
        if [[ -f .env ]]; then
            set -a
            # shellcheck disable=SC1091
            source .env
            set +a
        fi
        # stdin с /dev/tty: create_SuperAdminUser и др. при curl|bash
        if [[ -r /dev/tty ]]; then
            .venv/bin/python "$@" </dev/tty
        else
            .venv/bin/python "$@"
        fi
    )
}

deploy_backend() {
    if [[ ! -x "${BACKEND_DEPLOY_SCRIPT}" && -f "${BACKEND_DEPLOY_SCRIPT}" ]]; then
        chmod +x "${BACKEND_DEPLOY_SCRIPT}"
    fi
    if [[ ! -f "${BACKEND_DEPLOY_SCRIPT}" ]]; then
        log_error "Скрипт не найден: ${BACKEND_DEPLOY_SCRIPT}"
        exit 1
    fi

    log_info "Запуск deploy_backend.sh..."
    # stdin с /dev/tty: при curl|bash иначе интерактивные read в дочернем скрипте падают
    if [[ -r /dev/tty ]]; then
        bash "${BACKEND_DEPLOY_SCRIPT}" </dev/tty
    else
        bash "${BACKEND_DEPLOY_SCRIPT}"
    fi

    echo
    echo "──────────────────────────────────────────────"
    echo " Создание учётной записи SUPERADMIN"
    echo "──────────────────────────────────────────────"
    echo "  [y] — создать сейчас (интерактивный ввод)"
    echo "  [n] — пропустить (позже:"
    echo "        cd ${BACKEND_DIR} && .venv/bin/python additional_scripts/create_SuperAdminUser.py)"
    echo "──────────────────────────────────────────────"

    local create_admin_answer=""
    while true; do
        read_from_tty create_admin_answer "Создать SUPERADMIN сейчас? [y/N]: " "N"
        create_admin_answer="${create_admin_answer:-N}"
        case "${create_admin_answer}" in
            [yY]|[yY][eE][sS]|[дД]|[дД][аА])
                log_info "Запуск create_SuperAdminUser.py..."
                run_backend_python additional_scripts/create_SuperAdminUser.py
                break
                ;;
            [nN]|[nN][oO]|[нН]|[нН][еЕ][тТ]|"")
                log_warn "Создание SUPERADMIN пропущено."
                break
                ;;
            *)
                log_warn "Введите y (да) или n (нет)."
                ;;
        esac
    done

    if [[ -f "${BACKEND_SCRIPTS_DIR}/seed_templates_vCard.py" ]]; then
        log_info "Сидинг шаблонов визиток..."
        run_backend_python additional_scripts/seed_templates_vCard.py || log_warn "Сид шаблонов завершился с ошибкой."
    fi
}

deploy_frontend() {
    if [[ ! -x "${FRONTEND_DEPLOY_SCRIPT}" && -f "${FRONTEND_DEPLOY_SCRIPT}" ]]; then
        chmod +x "${FRONTEND_DEPLOY_SCRIPT}"
    fi
    if [[ ! -f "${FRONTEND_DEPLOY_SCRIPT}" ]]; then
        log_error "Скрипт не найден: ${FRONTEND_DEPLOY_SCRIPT}"
        exit 1
    fi

    log_info "Запуск deploy_frontend.sh..."
    if [[ -r /dev/tty ]]; then
        bash "${FRONTEND_DEPLOY_SCRIPT}" </dev/tty
    else
        bash "${FRONTEND_DEPLOY_SCRIPT}"
    fi
}

usage() {
    cat <<EOF
Использование: $0 [команда]

  (без аргументов)  Полная установка: git, backend, frontend
  --check | check   Версии в main / dev / текущей (без изменений кода)
  --update | update Проверить версии и обновить/перезапустить при необходимости
  --force-update    Принудительно обновить backend и frontend
  -h | --help       Справка
EOF
}

full_install() {
    log_info "=== Начало развёртывания Digital Business Card Service ==="
    check_root
    check_os
    preinstall_system_pkg
    select_git_branch
    clone_repository
    deploy_backend
    deploy_frontend
    print_versions
    log_info "=== Развёртывание завершено ==="
}

main() {
    local cmd="${1:-install}"

    case "${cmd}" in
        -h|--help|help)
            usage
            trap - EXIT
            exit 0
            ;;
        --check|check)
            check_root
            print_check_versions
            trap - EXIT
            exit 0
            ;;
        --update|update)
            check_root
            check_and_update_versions 0
            trap - EXIT
            exit 0
            ;;
        --force-update|force-update)
            check_root
            check_and_update_versions 1
            trap - EXIT
            exit 0
            ;;
        install|"")
            full_install
            trap - EXIT
            exit 0
            ;;
        *)
            log_error "Неизвестная команда: ${cmd}"
            usage
            exit 1
            ;;
    esac
}

main "$@"

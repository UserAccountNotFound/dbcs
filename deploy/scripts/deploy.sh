#!/usr/bin/env bash
#
# deploy.sh
# Идемпотентный скрипт развертывания backend-части DBCS для Debian.
#
#
# Использование:
#   sudo bash deploy.sh
#
# Примеры:
#   sudo env APP_ROOT=/opt/dbcs bash deploy.sh
#   sudo env APP_USER=dbcs bash deploy.sh
#   sudo env APT_UPGRADE=1 PIP_UPGRADE=1 APP_USER=dbcs bash deploy.sh
#   sudo env FORCE_ENV_OVERWRITE=1 bash deploy.sh

set -Eeuo pipefail


# ============================================================
# Пути и конфигурация
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Если скрипт лежит в /DBCS/deploy/scripts/deploy.sh,
# APP_ROOT автоматически станет /DBCS.
APP_ROOT="${APP_ROOT:-$(cd "$SCRIPT_DIR/../.." && pwd)}"

BACKEND_DIR="${BACKEND_DIR:-$APP_ROOT/backend}"
VENV_DIR="$BACKEND_DIR/.venv"
REQUIREMENTS_FILE="$BACKEND_DIR/requirements.txt"
ENV_FILE="$BACKEND_DIR/.env"
ENV_EXAMPLE_FILE="$BACKEND_DIR/.env.example"

# Обновление системных пакетов по умолчанию отключено.
# Для production обычно лучше управлять этим отдельно.
APT_UPGRADE="${APT_UPGRADE:-0}"

# Обновление pip по умолчанию отключено для большей идемпотентности.
PIP_UPGRADE="${PIP_UPGRADE:-0}"

# Если нужно принудительно перезаписать .env из .env.example:
# FORCE_ENV_OVERWRITE=1
FORCE_ENV_OVERWRITE="${FORCE_ENV_OVERWRITE:-0}"

# Если приложение должно работать от отдельного пользователя,
# задай APP_USER, например:
#   sudo env APP_USER=dbcs bash deploy.sh
APP_USER="${APP_USER:-}"

APT_UPDATED=0

REQUIRED_PACKAGES=(
  git
  curl
  ca-certificates
  python3
  python3-venv
  mariadb-server
  mariadb-client
)


# ============================================================
# Логирование и ошибки
# ============================================================

log() {
  printf '[deploy] %s\n' "$*"
}

err() {
  printf '[deploy][error] %s\n' "$*" >&2
}

die() {
  err "$@"
  exit 1
}

trap 'err "Deploy failed on line $LINENO"' ERR


# ============================================================
# Helpers
# ============================================================

is_true() {
  local value="${1:-}"
  [[ "${value,,}" =~ ^(1|true|yes|on)$ ]]
}

require_root() {
  if [[ $EUID -ne 0 ]]; then
    die "Run script as root/sudo, for example: sudo bash $0"
  fi
}

file_exists() {
  [[ -f "$1" ]]
}

dir_exists() {
  [[ -d "$1" ]]
}

require_file() {
  file_exists "$1" || die "Required file not found: $1"
}

package_installed() {
  dpkg -s "$1" >/dev/null 2>&1
}


# ============================================================
# APT
# ============================================================

apt_update_once() {
  if [[ "$APT_UPDATED" -eq 1 ]]; then
    return 0
  fi

  export DEBIAN_FRONTEND=noninteractive

  log "Updating APT package lists..."
  apt-get update

  APT_UPDATED=1
}

maybe_upgrade_packages() {
  if ! is_true "$APT_UPGRADE"; then
    log "Skipping apt upgrade. Set APT_UPGRADE=1 to enable."
    return 0
  fi

  apt_update_once

  export DEBIAN_FRONTEND=noninteractive

  log "Upgrading Debian packages..."
  apt-get upgrade -y \
    -o Dpkg::Options::=--force-confdef \
    -o Dpkg::Options::=--force-confold \
    --no-install-recommends
}

ensure_packages() {
  local missing=()
  local pkg

  for pkg in "${REQUIRED_PACKAGES[@]}"; do
    if ! package_installed "$pkg"; then
      missing+=("$pkg")
    fi
  done

  if [[ ${#missing[@]} -eq 0 ]]; then
    log "All required Debian packages are already installed."
    return 0
  fi

  apt_update_once

  export DEBIAN_FRONTEND=noninteractive

  log "Installing missing packages: ${missing[*]}"
  apt-get install -y \
    -o Dpkg::Options::=--force-confdef \
    -o Dpkg::Options::=--force-confold \
    --no-install-recommends \
    "${missing[@]}"
}


# ============================================================
# Python venv
# ============================================================

ensure_venv() {
  local current_python
  local marker="$VENV_DIR/.deploy_python_version"
  local venv_ok=0

  current_python="$(python3 -c 'import platform; print(platform.python_version())')"

  if [[ -x "$VENV_DIR/bin/python" ]] && "$VENV_DIR/bin/python" -c 'import sys' >/dev/null 2>&1; then
    venv_ok=1
  fi

  # Если версия системного Python изменилась, venv лучше пересоздать.
  if [[ "$venv_ok" -eq 1 && -f "$marker" ]]; then
    if [[ "$(cat "$marker")" != "$current_python" ]]; then
      log "Python version changed. Recreating virtualenv..."
      rm -rf "$VENV_DIR"
      venv_ok=0
    fi
  fi

  if [[ "$venv_ok" -eq 0 ]]; then
    log "Creating virtualenv: $VENV_DIR"
    rm -rf "$VENV_DIR"
    python3 -m venv "$VENV_DIR"
  else
    log "Virtualenv already exists: $VENV_DIR"
  fi

  printf '%s\n' "$current_python" > "$marker"
}

ensure_pip() {
  if "$VENV_DIR/bin/python" -m pip --version >/dev/null 2>&1; then
    return 0
  fi

  log "pip is missing in virtualenv, bootstrapping..."
  "$VENV_DIR/bin/python" -m ensurepip --upgrade
}

install_python_dependencies() {
  if is_true "$PIP_UPGRADE"; then
    log "Upgrading pip..."
    "$VENV_DIR/bin/python" -m pip install --disable-pip-version-check --upgrade pip
  fi

  log "Installing Python requirements..."
  "$VENV_DIR/bin/python" -m pip install --disable-pip-version-check -r "$REQUIREMENTS_FILE"
}


# ============================================================
# .env
# ============================================================

ensure_env_file() {
  if file_exists "$ENV_FILE" && ! is_true "$FORCE_ENV_OVERWRITE"; then
    log ".env already exists and will not be overwritten."
  else
    require_file "$ENV_EXAMPLE_FILE"

    log "Creating .env from .env.example"
    install -m 600 "$ENV_EXAMPLE_FILE" "$ENV_FILE"
  fi

  chmod 600 "$ENV_FILE"
}


# ============================================================
# Права доступа
# ============================================================

set_owner_if_needed() {
  local group

  if [[ -z "$APP_USER" ]]; then
    log "WARNING: APP_USER is not set. Created files are owned by root."
    log "For production, set APP_USER=<service_user> if the app runs under a dedicated user."
    return 0
  fi

  id "$APP_USER" >/dev/null 2>&1 || die "APP_USER '$APP_USER' does not exist"

  group="$(id -gn "$APP_USER")"

  log "Setting ownership of backend artifacts to user: $APP_USER"
  chown -R "$APP_USER:$group" "$VENV_DIR"
  chown "$APP_USER:$group" "$ENV_FILE"
}


# ============================================================
# Проверки перед деплоем
# ============================================================

preflight_checks() {
  dir_exists "$BACKEND_DIR" || die "Backend directory not found: $BACKEND_DIR"
  require_file "$REQUIREMENTS_FILE"

  if ! file_exists "$ENV_FILE" || is_true "$FORCE_ENV_OVERWRITE"; then
    require_file "$ENV_EXAMPLE_FILE"
  fi
}


# ============================================================
# Main
# ============================================================

main() {
  log "APP_ROOT=$APP_ROOT"
  log "BACKEND_DIR=$BACKEND_DIR"

  preflight_checks
  require_root

  maybe_upgrade_packages
  ensure_packages
  ensure_venv
  ensure_pip
  install_python_dependencies
  ensure_env_file
  set_owner_if_needed

  log "Deployment completed successfully."
}

main "$@"
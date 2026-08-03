#!/usr/bin/env bash

# Скрипт автоматизированного развертывания DBCS
# /DBCS/deploy/scripts/deploy.sh
# version 1.0.0

# Строгий режим выполнения
set -euo pipefail


# обновляем систему до апстрима и ставим необходимые пакеты
apt update && apt upgrade -y
apt install git curl python3

python -m venv backend/.venv
source backend/.venv/bin/activate
python -m pip install --upgrade pip
pip install -r backend/requirements.txt

cp backend/.env.example backend/.env
# Структура прав
```
backend/
├── .env                          # 600 (rw-------)
├── .venv/                        # 755 (исключён из общей обработки)
│   └── bin/
│       └── python                # 755
├── app/
│   ├── __init__.py               # 644 (rw-r--r--)
│   └── main.py                   # 755 (исполняемый .py)
├── scripts/
│   ├── deploy.sh                 # 755 (исполняемый .sh)
│   └── backup.sh                 # 755
├── requirements.txt              # 644
└── README_backend.md             # 644
```


# Сервис визитных карточек app/services/card_service.py
# Endpoints для визиток app/api/cards.py


# Создание новой учетной записи SUPERADMIN в БД

- Запуск скрипта от имени пользователя приложения
```
sudo -u ecard bash -c "cd /opt/dbcs/backend && set -a && source .env && set +a && .venv/bin/python create_SuperAdminUser.py"
```
- если в dev-режиме из-под root:
```
cd /opt/dbcs/backend
source .venv/bin/activate
set -a && source .env && set +a
python create_superuser.py
```
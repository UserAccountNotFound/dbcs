# Ops: права и служебные команды

## Права на файлы (ориентир)

```
backend/
├── .env                          # 600 (rw-------)
├── .venv/                        # 755 (venv не «выравнивать» рекурсивно вместе с app)
│   └── bin/python                # 755
├── app/                          # код: обычно 644 для .py, каталоги 755
├── additional_scripts/
│   ├── deploy_backend.sh         # 755
│   ├── create_SuperAdminUser.py
│   ├── seed_templates_vCard.py
│   └── run_backup.py
├── requirements.txt              # 644
├── README.md                     # 644
└── README_backend.md             # 644
```

Пользователь сервиса на установке через `install.sh` / deploy: обычно `ecard`. Unit: `dbcs-backend.service`.

## SuperAdmin и seed шаблонов

От имени пользователя приложения:

```bash
sudo -u ecard bash -c 'cd /opt/dbcs/backend && set -a && source .env && set +a && .venv/bin/python additional_scripts/create_SuperAdminUser.py'
sudo -u ecard bash -c 'cd /opt/dbcs/backend && set -a && source .env && set +a && .venv/bin/python additional_scripts/seed_templates_vCard.py'
```

В dev из-под root:

```bash
cd /opt/dbcs/backend
source .venv/bin/activate
set -a && source .env && set +a
python additional_scripts/create_SuperAdminUser.py
python additional_scripts/seed_templates_vCard.py
```

## Карточки

- Сервис: `app/services/card_service.py`
- API: `app/api/cards.py`
- Публичка: `app/api/public_cards.py`, `app/services/public_card_service.py`
- vCard / QR: `app/services/vcard_service.py`, `app/services/qr_service.py`

## Бэкап

- Настройки и API: админка SuperAdmin → Backup (`/api/v1/admin/settings/backup…`)
- CLI runner: `additional_scripts/run_backup.py` (с загруженным `.env`)

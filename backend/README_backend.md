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
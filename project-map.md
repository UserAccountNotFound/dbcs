```
dbcs/
├── backend/                  # Python API
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── main.py
│   ├── alembic/
│   ├── tests/
│   ├── pyproject.toml
│   └── alembic.ini
│
├── frontend/                 # PWA: личный кабинет + админка + публичные визитки
│   ├── src/
│   │   ├── api/
│   │   ├── app/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── router/
│   │   ├── stores/
│   │   ├── pwa/
│   │   └── main.ts
│   ├── public/
│   ├── index.html
│   ├── package.json
│   └── vite.config.ts
│
├── deploy/
│   ├── nginx/
│   │   └── e-cards.conf
│   ├── systemd/
│   │   ├── e-cards-backend.service
│   │   └── e-cards-migrations.service
│   ├── scripts/
│   │   ├── deploy.sh
│   │   ├── backup-db.sh
│   │   └── migrate.sh
│   └── env/
│       └── backend.env.example
│
└── docs/
    ├── architecture.md
    ├── security.md
    ├── database.md
    └── api/
        └── redoc.md
```

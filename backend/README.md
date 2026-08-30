# Документация backend

Backend DBCS: **FastAPI** + **SQLAlchemy 2.0** + **Alembic**, MySQL/MariaDB.

Версия API (`app_version`): см. `app/core/config.py` (сейчас `1.4.1`).

## Структура

```
backend/
├── app/
│   ├── main.py                 # Точка входа FastAPI
│   ├── api/
│   │   ├── router.py           # Сборка роутеров
│   │   ├── deps.py             # DI: db, current user / admin / superadmin
│   │   ├── auth.py
│   │   ├── cards.py
│   │   ├── public_cards.py
│   │   ├── templates.py
│   │   ├── files.py
│   │   ├── admin.py
│   │   ├── health.py
│   │   └── schemas/            # Pydantic-схемы
│   ├── core/
│   │   ├── config.py           # Settings из .env
│   │   ├── security.py         # Argon2, dummy-hash для login timing
│   │   ├── tokens.py           # JWT
│   │   └── urls.py
│   ├── db/                     # session, base, init
│   ├── models/                 # ORM
│   └── services/               # Бизнес-логика
├── alembic/
├── templates/css/              # CSS-шаблоны ({code}.css) + README
├── additional_scripts/
│   ├── deploy_backend.sh
│   ├── create_SuperAdminUser.py
│   ├── seed_templates_vCard.py
│   └── run_backup.py
├── requirements.txt
├── .env.example
├── README.md
└── README_backend.md           # Права файлов и ops-заметки
```

## Установка (dev)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# заполнить DATABASE_URL и SECRET_KEY (≥ 32 символов)

alembic upgrade head
python additional_scripts/create_SuperAdminUser.py
python additional_scripts/seed_templates_vCard.py
```

## Конфигурация

См. `.env.example`. Важное:

```env
DATABASE_URL=mysql+pymysql://user:password@127.0.0.1:3306/e_cards?charset=utf8mb4
SECRET_KEY=...at-least-32-chars...
ALLOWED_ORIGINS=http://localhost:5173
PUBLIC_BASE_URL=http://localhost:5173

UPLOADS_DIR=/var/lib/dbcs/uploads
BACKUP_DIR_DEFAULT=/var/lib/dbcs/backups
# TEMPLATES_CSS_DIR=/opt/dbcs/backend/templates/css

ACCESS_TOKEN_TTL_MINUTES=15
REFRESH_TOKEN_TTL_DAYS=7
SELF_REGISTRATION_ENABLED=true

REFRESH_COOKIE_SECURE=false          # prod: true (+ HTTPS)
REFRESH_COOKIE_SAMESITE=lax

DOCS_ENABLED=true
REDOC_ENABLED=true
```

OpenAPI docs также переключаются из админки (SuperAdministrator → Settings).

## Запуск

```bash
# Development
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production (типично через systemd + gunicorn; см. deploy_backend.sh)
```

## API (`/api/v1`)

Health: `GET /api/v1/health` → `{ "status": "ok", "environment": "...", "version": "..." }`.

Docs (если включены): `/api/docs`, `/api/redoc`.

### Auth `/auth`
| Method | Path | Описание |
|--------|------|----------|
| POST | `/register` | Регистрация |
| POST | `/login` | Вход |
| POST | `/refresh` | Silent refresh |
| POST | `/logout` | Выход |
| GET | `/me` | Текущий пользователь |

### Cards `/cards` (auth)
| Method | Path | Описание |
|--------|------|----------|
| GET/POST | `/` | Список / создание |
| GET/PATCH/DELETE | `/{card_id}` | CRUD |
| GET | `/{card_id}/qrcode.svg` | QR |
| GET | `/{card_id}/vcard.vcf` | vCard |
| GET | `/{card_id}/stats` | Статистика |
| POST | `/{card_id}/regenerate-slug` | Новый slug |
| GET | `/export` | Экспорт (`format=json\|csv`) |
| POST | `/import` | Импорт |

### Public `/public/cards`
| Method | Path | Описание |
|--------|------|----------|
| GET | `/{slug}` | Публичная визитка |
| GET | `/{slug}/qrcode.svg` | QR |
| GET | `/{slug}/vcard.vcf` | vCard |
| GET | `/{slug}/avatar`, `/{slug}/logo` | Медиа |

### Templates `/templates`
| Method | Path | Auth | Описание |
|--------|------|------|----------|
| GET | `/` | ✅ | Активные шаблоны |
| GET | `/{template_id}` | ✅ | По id |
| GET | `/{code}/css` | публично | CSS файл шаблона |

### Files `/files` (auth)
| Method | Path | Описание |
|--------|------|----------|
| POST | `/upload` | Загрузка |
| GET/DELETE | `/{file_id}` | Получение / удаление |

### Admin `/admin`
| Method | Path | Роль | Описание |
|--------|------|------|----------|
| GET/POST | `/users` | Admin+ | Список / создание |
| PATCH | `/users/{id}` | Admin+* | Обновление (*роли ADMIN/SUPERADMIN — только SuperAdmin) |
| DELETE | `/users/{id}` | SuperAdmin | Удаление |
| GET | `/cards` | Admin+ | Все визитки |
| POST | `/cards/{id}/deactivate` | Admin+ | Деактивация |
| GET/POST/PATCH/DELETE | `/templates...` | Admin+ | CRUD шаблонов, CSS, toggle |
| GET | `/audit` | Admin+ | Журнал |
| GET | `/analytics/extended`, `/stats/overview` | Admin+ | Аналитика |
| GET/PATCH/POST | `/settings/backup...` | SuperAdmin | Бэкап / restore / run |
| GET/PATCH/POST | `/settings/smtp...` | SuperAdmin | SMTP + test |
| GET/PATCH | `/settings/docs` | SuperAdmin | Вкл/выкл docs |

## Модели (кратко)

### User
`id`, `email`, `password_hash`, `full_name`, `role` (`USER`\|`ADMIN`\|`SUPERADMIN`), `is_active`, timestamps.

### Card
`id`, `user_id`, `template_id`, `slug`, `title`, `full_name`, `job_title`, `department`, `company`,  
`phone`, `phone_additional`, messengers (`telegram`, `whatsapp`, `viber`, `wechat`, `messenger_max`, `discord`, `vk`),  
`email`, `website`, `address`, `note`, `theme` (JSON), `avatar_file_id`, `logo_file_id`, `is_active`, `deleted_at`, timestamps.

`theme`: `color_scheme`, `layout`, `font`, `accent_color`, `show_photo`, `show_qr`.

### CardTemplate
`code` (имя CSS-файла), `name`, `description`, `preview_image`, `schema_json` (meta: `default_accent`, `default_scheme`, `effect`), `is_active`.

CSS лежит в `templates/css/{code}.css` — контракт классов: [templates/css/README.md](templates/css/README.md).

### Прочее
`CardVisit`, `AuthSession`, `AuditLog`, `File`, `BackupSettings`, `SmtpSettings`, `SystemSettings`.

## Шаблоны визиток

- HTML-каркас один (`PublicCardRenderer` на frontend).
- Визуал — CSS на диске; раздача: `GET /api/v1/templates/{code}/css`.
- Seed: `python additional_scripts/seed_templates_vCard.py`.

## Безопасность

- Access JWT + refresh HttpOnly cookie с ротацией
- Пароли Argon2id; выравнивание времени login при неизвестном email
- Роли: User / Administrator / SuperAdministrator
- Валидация website и messenger URL (allowlist схем)
- SMTP test не подставляет сохранённый пароль к «чужому» host/port/TLS

## Миграции

```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
alembic downgrade -1
alembic current
```

> `alembic/README` описывает **greenfield**-сценарий (удаление versions и генерация с нуля). На живой БД так не делать.

## Развёртывание

```bash
sudo bash additional_scripts/deploy_backend.sh
```

Обычно: пользователь `ecard`, unit `dbcs-backend.service`, gunicorn на `127.0.0.1:8000`, nginx проксирует `/api`.

### Production чеклист
- [ ] `SECRET_KEY` уникальный и длинный
- [ ] `DEBUG=false`, `ENVIRONMENT=production`
- [ ] `ALLOWED_ORIGINS` и `PUBLIC_BASE_URL` корректны
- [ ] `REFRESH_COOKIE_SECURE=true` при HTTPS
- [ ] HTTPS / TLS
- [ ] Бэкапы (админка или cron + `run_backup.py`)
- [ ] Docs отключены снаружи при необходимости

## Ops: SuperAdmin и seed

См. также [README_backend.md](README_backend.md):

```bash
cd /opt/dbcs/backend
source .venv/bin/activate
set -a && source .env && set +a
python additional_scripts/create_SuperAdminUser.py
python additional_scripts/seed_templates_vCard.py
```

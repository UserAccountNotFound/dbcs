![Stability](https://img.shields.io/badge/stability-work_in_progress-lightgrey?style=flat&color=ffff00)

![GitHub repo size](https://img.shields.io/github/repo-size/UserAccountNotFound/dbcs?style=flat)

# DBCS - Digital Business Card Service

Сервис цифровых визитных карточек с QR-кодами и экспортом в vCard.

По факту просто попытка изобрести свой - "аналогов нет" велосипед с преферансом и поэтессами

Версии (примерно): backend `1.4.1`, frontend `1.4.5`.

![Linux](https://img.shields.io/badge/-Linux-6C6694.svg?logo=linux&style=flat)
![Python](https://img.shields.io/badge/-Python-F9DC3E.svg?logo=Python&style=flat)
![Vue.js](https://img.shields.io/badge/-Vue.js-4FC08D.svg?logo=vue.js&style=flat)
![FastAPI](https://img.shields.io/badge/-FastAPI-009688.svg?logo=fastapi&style=flat)

## Оглавление

- [Возможности](#-возможности)
- [Архитектура](#-архитектура)
- [Быстрый старт](#-быстрый-старт)
- [Конфигурация](#-конфигурация)
- [API](#-api)
- [Модели данных](#-модели-данных)
- [Безопасность](#-безопасность)
- [Развёртывание](#-развёртывание)
- [Структура проекта](#-структура-проекта)

## Возможности

### Для пользователей
- Создание и редактирование цифровых визиток
- CSS-шаблоны оформления (каркас HTML фиксирован, визуал — CSS на диске)
- Персонализация темы: акцент, светлая/тёмная схема, шрифт, фото и QR
- Контакты: телефоны, email, сайт, адрес, заметка
- Мессенджеры и соцсети: Telegram, WhatsApp, Viber, WeChat, Max, Discord, VK
- Генерация QR-кодов и экспорт в vCard (`.vcf`)
- Статистика просмотров своей визитки
- Загрузка аватара и логотипа
- Экспорт / импорт визиток (JSON / CSV)
- Интерфейс на русском и английском (`vue-i18n`, переключатель в UI)

### Для администраторов
- Управление пользователями (создание, роли, деактивация; удаление — только SuperAdministrator)
- Управление шаблонами и загрузка CSS
- Обзор визиток и деактивация
- Аналитика и журнал аудита
- SuperAdministrator: резервное копирование / восстановление, SMTP, включение/выключение OpenAPI docs

### Технические особенности
- JWT access + refresh в HttpOnly cookie с ротацией
- Роли: `USER` / `ADMIN` / `SUPERADMIN` (в UI: User, Administrator, SuperAdministrator)
- Публичные визитки по slug без авторизации
- PWA (vite-plugin-pwa)
- REST API; Swagger/ReDoc можно отключить в админ-настройках

## Архитектура

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Frontend      │────▶│     Backend      │────▶│   Database      │
│   Vue 3 + TS    │◀────│     FastAPI      │◀────│   MySQL/MariaDB │
│   Pinia + Axios │     │   SQLAlchemy 2   │     │                 │
│   vue-i18n      │     │   Gunicorn       │     │                 │
└─────────────────┘     └──────────────────┘     └─────────────────┘
         ▲                        ▲
         └──────── nginx ─────────┘
```

| Компонент | Технология |
|-----------|------------|
| Backend | Python 3.10+, FastAPI, SQLAlchemy 2.0, Alembic |
| Frontend | Vue 3, TypeScript, Pinia, Vue Router, vue-i18n, TailwindCSS, Vite |
| Database | MySQL 8.0+ / MariaDB 10.5+ |
| Auth | JWT (PyJWT), Argon2id |
| Proxy | nginx (статика frontend + `/api` → backend) |

## Быстрый старт

```bash
# Надёжнее: скачать файл, затем запустить (stdin свободен для вопросов)
curl -fsSL https://raw.githubusercontent.com/UserAccountNotFound/dbcs/main/install.sh -o /tmp/dbcs-install.sh
sudo bash /tmp/dbcs-install.sh

# Или одной строкой (вопросы идут через /dev/tty)
curl -fsSL https://raw.githubusercontent.com/UserAccountNotFound/dbcs/main/install.sh | sudo bash

# Без вопросов: ветка main|dev
DBCS_BRANCH=main curl -fsSL https://raw.githubusercontent.com/UserAccountNotFound/dbcs/main/install.sh | sudo bash
```

> URL должен быть `raw.githubusercontent.com`. Без `-L`/`-f` старый URL `github.com/.../raw/...` может отдать пустой 302.

### Предварительные требования
- Python 3.10+
- Node.js 18+ и npm
- MySQL 8.0+ или MariaDB 10.5+

### Backend (dev)
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # заполнить SECRET_KEY и DATABASE_URL
alembic upgrade head
python additional_scripts/create_SuperAdminUser.py
python additional_scripts/seed_templates_vCard.py
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend (dev)
```bash
cd frontend
npm install
cp .env.example .env   # VITE_API_BASE_URL=/api/v1
npm run dev            # http://localhost:5173 (proxy /api → :8000)
```

Подробнее: [backend/README.md](backend/README.md), [frontend/README.md](frontend/README.md).

## Конфигурация

Основные переменные backend (см. `backend/.env.example`):

| Переменная | Описание |
|------------|----------|
| `DATABASE_URL` | URL БД (`mysql+pymysql://...`) |
| `SECRET_KEY` | Секрет JWT (≥ 32 символов) |
| `ALLOWED_ORIGINS` | CORS origins (через запятую или JSON-массив) |
| `PUBLIC_BASE_URL` | Базовый URL для публичных ссылок визиток |
| `ACCESS_TOKEN_TTL_MINUTES` | TTL access token (по умолчанию 15) |
| `REFRESH_TOKEN_TTL_DAYS` | TTL refresh cookie (по умолчанию 7) |
| `UPLOADS_DIR` | Каталог загрузок |
| `TEMPLATES_CSS_DIR` | Каталог CSS-шаблонов (по умолчанию `backend/templates/css`) |
| `DOCS_ENABLED` / `REDOC_ENABLED` | OpenAPI UI (можно менять и из админки) |
| `SELF_REGISTRATION_ENABLED` | Самостоятельная регистрация |
| `REFRESH_COOKIE_SECURE` | Secure-флаг cookie (в prod обычно `true`) |

Frontend: `VITE_API_BASE_URL=/api/v1` (`frontend/.env.example`).

## API

Префикс: `/api/v1`. Документация (если включена):
- Swagger: `{origin}/api/docs`
- ReDoc: `{origin}/api/redoc`
- Health: `GET /api/v1/health`

### Auth `/api/v1/auth`
| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/register` | Регистрация (если разрешена) |
| POST | `/login` | Вход |
| POST | `/refresh` | Обновление access token |
| POST | `/logout` | Выход |
| GET | `/me` | Текущий пользователь |

### Cards `/api/v1/cards`
| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/` | Список своих визиток |
| POST | `/` | Создание |
| GET | `/{id}` | Получение |
| PATCH | `/{id}` | Обновление |
| DELETE | `/{id}` | Удаление |
| GET | `/{id}/qrcode.svg` | QR |
| GET | `/{id}/vcard.vcf` | vCard |
| GET | `/{id}/stats` | Статистика |
| POST | `/{id}/regenerate-slug` | Новый slug |
| GET | `/export` | Экспорт JSON/CSV |
| POST | `/import` | Импорт |

### Public `/api/v1/public/cards`
| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/{slug}` | Публичная визитка |
| GET | `/{slug}/qrcode.svg` | QR |
| GET | `/{slug}/vcard.vcf` | vCard |
| GET | `/{slug}/avatar` / `/logo` | Медиа |

### Templates `/api/v1/templates`
| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/` | Список активных шаблонов (auth) |
| GET | `/{id}` | Шаблон по id (auth) |
| GET | `/{code}/css` | CSS шаблона (публично) |

Админские эндпоинты: `/api/v1/admin/...` (users, cards, templates, audit, analytics, backup, smtp, docs) — см. [backend/README.md](backend/README.md).

## Модели данных

- **User** — email, password_hash, role, is_active
- **Card** — slug, контакты, мессенджеры, theme (JSON), template_id, avatar/logo
- **CardTemplate** — code, name, schema_json (meta: accent/scheme/effect), CSS на диске по `code`
- **CardVisit** — статистика просмотров (хэши PII)
- **AuthSession** — refresh-сессии
- **AuditLog** — журнал действий
- **File** — загруженные файлы
- **BackupSettings** / **SmtpSettings** / **SystemSettings** — системные настройки

## Безопасность

- Access token: JWT ~15 мин (localStorage / память клиента)
- Refresh token: HttpOnly cookie, ротация
- Пароли: Argon2id
- PII в визитах/аудите: хэширование
- Ссылки мессенджеров/сайта: allowlist схем (`http`/`https`/`viber`/`tg`/…)
- Назначение ролей `ADMIN`/`SUPERADMIN` — только SuperAdministrator

## Развёртывание

Скрипты лежат рядом с приложениями (каталога `deploy/` нет):

```bash
# Backend (systemd unit dbcs-backend, миграции, права)
sudo bash backend/additional_scripts/deploy_backend.sh

# Frontend (build → /var/www/dbcs/frontend, nginx)
sudo bash frontend/additional_scripts/deploy_frontend.sh
```

Установка «с нуля» на сервер: корневой `install.sh`.

## Структура проекта

```
dbcs/
├── install.sh
├── backend/
│   ├── app/                    # FastAPI приложение
│   ├── alembic/                # Миграции
│   ├── templates/css/          # CSS-шаблоны визиток
│   ├── additional_scripts/     # deploy, seed, create SuperAdmin, backup runner
│   └── README.md
├── frontend/
│   ├── src/                    # Vue 3 приложение
│   ├── additional_scripts/     # deploy_frontend.sh
│   └── README.md
├── backups/                    # Локальные бэкапы (не в git)
└── README.md
```

# Contributing
Кроме меня этот говнокод ни кому не нужон. =)

# License
Проект распространяется под MIT — подробности в файле [LICENSE](LICENSE).

# Acknowledgments
Особая благодарность всем проектам с открытым исходным кодом и людям, что готовы делиться знаниями.

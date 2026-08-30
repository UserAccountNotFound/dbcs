#  Документация к backend

## Обзор

Backend сервиса построен на **FastAPI** с использованием **SQLAlchemy 2.0** для работы с базой данных.

## Структура проекта

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # Точка входа FastAPI приложения
│   ├── api/                    # API endpoints
│   │   ├── __init__.py
│   │   ├── router.py           # Объединение всех роутеров
│   │   ├── deps.py             # Зависимости (DI)
│   │   ├── auth.py             # Аутентификация и авторизация
│   │   ├── cards.py            # CRUD операции с визитками
│   │   ├── public_cards.py     # Публичный доступ к визиткам
│   │   ├── templates.py        # Управление шаблонами
│   │   ├── files.py            # Загрузка и управление файлами
│   │   ├── admin.py            # Админские эндпоинты
│   │   ├── health.py           # Health check endpoint
│   │   └── schemas/            # Pydantic схемы для API
│   │       ├── __init__.py
│   │       ├── auth.py
│   │       ├── card.py
│   │       ├── public_card.py
│   │       ├── template.py
│   │       ├── file.py
│   │       ├── admin.py
│   │       ├── stats.py
│   │       └── common.py
│   ├── core/                   # Ядро приложения
│   │   ├── __init__.py
│   │   ├── config.py           # Настройки приложения
│   │   ├── security.py         # Хеширование, верификация
│   │   ├── tokens.py           # JWT токены
│   │   └── utils.py            # Утилиты
│   ├── db/                     # Работа с БД
│   │   ├── __init__.py
│   │   ├── base.py             # Базовые классы ORM
│   │   ├── session.py          # Сессии SQLAlchemy
│   │   └── init_db.py          # Инициализация БД
│   ├── models/                 # SQLAlchemy модели
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── card.py
│   │   ├── card_template.py
│   │   ├── card_visit.py
│   │   ├── auth_session.py
│   │   ├── audit_log.py
│   │   └── file.py
│   └── services/               # Бизнес-логика
│       ├── __init__.py
│       ├── user_service.py
│       ├── card_service.py
│       ├── auth_service.py
│       ├── audit_service.py
│       ├── file_service.py
│       ├── template_service.py
│       └── exceptions.py       # Кастомные исключения
├── alembic/                    # Миграции БД
│   ├── versions/
│   └── env.py
├── alembic.ini                 # Конфигурация Alembic
├── requirements.txt            # Python зависимости
├── create_SuperAdminUser.py    # Скрипт создания суперпользователя
├── seed_templates_vCard.py     # Скрипт заполнения шаблонов
└── README.md                   # Этот файл
```

## Установка

### Требования

- Python 3.10+
- MySQL 8.0+ или MariaDB 10.5+

### Шаги установки

```bash
# Создание виртуального окружения
python3 -m venv .venv
source .venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt

# Копирование примера окружения
cp .env.example .env

# Редактирование .env
nano .env

# Инициализация БД
alembic upgrade head

# Создание суперпользователя
python create_SuperAdminUser.py

# Заполнение шаблонами
python seed_templates_vCard.py
```

## Конфигурация

Основные переменные окружения в `.env`:

```env
# Database
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/dbcs_db

# Security
SECRET_KEY=your-secret-key-at-least-32-characters

# Environment
ENVIRONMENT=development
DEBUG=True

# CORS
ALLOWED_ORIGINS=http://localhost:5173

# Uploads
UPLOADS_DIR=/var/lib/dbcs/uploads
MAX_UPLOAD_SIZE_MB=5

# Tokens
ACCESS_TOKEN_TTL_MINUTES=15
REFRESH_TOKEN_TTL_DAYS=7

# Registration
SELF_REGISTRATION_ENABLED=False

# Cookie Security
REFRESH_COOKIE_SECURE=False
REFRESH_COOKIE_SAMESITE=lax

# Documentation
DOCS_ENABLED=True
REDOC_ENABLED=True
```

## Запуск

### Development

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Endpoints

### Аутентификация `/api/v1/auth`

| Endpoint | Method | Описание |
|----------|--------|----------|
| `/register` | POST | Регистрация |
| `/login` | POST | Вход |
| `/refresh` | POST | Обновление токена |
| `/logout` | POST | Выход |
| `/me` | GET | Текущий пользователь |

### Визитки `/api/v1/cards`

| Endpoint | Method | Описание | Auth |
|----------|--------|----------|------|
| `/` | GET | Список визиток | ✅ |
| `/` | POST | Создание | ✅ |
| `/{card_id}` | GET | Получение | ✅ |
| `/{card_id}` | PUT | Обновление | ✅ |
| `/{card_id}` | DELETE | Удаление | ✅ |
| `/{card_id}/qr` | GET | QR код | ✅ |
| `/{card_id}/vcard` | GET | Экспорт vCard | ✅ |
| `/{card_id}/stats` | GET | Статистика | ✅ |

### Публичные `/api/v1/public`

| Endpoint | Method | Описание |
|----------|--------|----------|
| `/cards/{public_id}` | GET | Публичная визитка |
| `/cards/{public_id}/visit` | POST | Регистрация посещения |

### Админка `/api/v1/admin`

| Endpoint | Method | Описание | Роль |
|----------|--------|----------|------|
| `/users` | GET | Список пользователей | Admin |
| `/users/{id}` | PUT | Обновление | Admin |
| `/users/{id}` | DELETE | Удаление | SuperAdmin |
| `/audit` | GET | Журнал аудита | Admin |
| `/analytics` | GET | Аналитика | Admin |

## Модели данных

### User
- `id`: UUID
- `email`: String (unique)
- `password_hash`: String
- `full_name`: String
- `role`: Enum (`USER` / User, `ADMIN` / Administrator, `SUPERADMIN` / SuperAdministrator)
- `is_active`: Boolean
- `created_at`, `updated_at`, `last_login_at`: DateTime

### Card
- `id`: UUID
- `user_id`: UUID (FK)
- `template_id`: UUID (FK)
- `public_id`: String (unique)
- `title`, `first_name`, `last_name`, `email`, `phone`, `company`, `position`: String
- `website`, `address`: String
- `bio`: Text
- `avatar_file_id`, `logo_file_id`: UUID (FK)
- `social_links`: JSON
- `is_active`: Boolean
- `created_at`, `updated_at`: DateTime

### CardTemplate
- `id`: UUID
- `name`: String
- `description`: Text
- `config`: JSON
- `is_active`: Boolean
- `created_at`: DateTime

### CardVisit
- `id`: UUID
- `card_id`: UUID (FK)
- `visited_at`: DateTime
- `ip_hash`, `user_agent_hash`, `referer`: String

### AuthSession
- `id`: UUID
- `user_id`: UUID (FK)
- `refresh_token_hash`: String
- `user_agent_hash`, `ip_hash`: String
- `created_at`, `expires_at`, `revoked_at`: DateTime

### AuditLog
- `id`: UUID
- `action`: String
- `actor_user_id`: UUID
- `entity_type`, `entity_id`: String
- `timestamp`: DateTime
- `ip_hash`, `user_agent_hash`: String
- `details`: JSON

### File
- `id`: UUID
- `user_id`: UUID (FK)
- `filename`, `original_filename`, `mime_type`: String
- `size_bytes`: Integer
- `storage_path`: String
- `created_at`: DateTime

## Безопасность

### Аутентификация
- Access token: JWT, 15 минут, в памяти клиента
- Refresh token: HttpOnly cookie, 7 дней, ротация при использовании

### Хеширование
- Пароли: Argon2id
- PII данные: SHA-256 с солью

### Роли
- **User** (`USER`): Базовый доступ к своим визиткам
- **Administrator** (`ADMIN`): + управление пользователями и шаблонами
- **SuperAdministrator** (`SUPERADMIN`): + назначение администраторов, удаление пользователей, резервное копирование и системные настройки

## Миграции БД

```bash
# Создать новую миграцию
alembic revision --autogenerate -m "Description"

# Применить миграции
alembic upgrade head

# Откатить последнюю миграцию
alembic downgrade -1

# Просмотреть статус
alembic current
```

## Тестирование

```bash
# Запуск тестов (будущая функциональность)
pytest tests/ -v

# Покрытие кода
pytest --cov=app tests/
```

## Линтинг

```bash
# Проверка стиля
flake8 app/

# Форматирование
black app/
isort app/
```

## Логирование

Логирование настроено через стандартный модуль `logging`. 
В production рекомендуется настроить вывод в файлы или syslog.

## Мониторинг

Health check endpoint: `GET /api/health`

Возвращает статус:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "database": "connected"
}
```

## Развёртывание

См. скрипт `../deploy/deploy_backend.sh`

### Production чеклист

- [ ] SECRET_KEY установлен и безопасен
- [ ] DEBUG = False
- [ ] ALLOWED_ORIGINS настроен
- [ ] REFRESH_COOKIE_SECURE = True
- [ ] HTTPS настроен
- [ ] Бэкапы БД настроены
- [ ] Логи настроены
- [ ] Мониторинг настроен

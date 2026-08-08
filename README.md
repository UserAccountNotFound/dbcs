![Stability](https://img.shields.io/badge/stability-work_in_progress-lightgrey?style=flat&color=ffff00)

![GitHub repo size](https://img.shields.io/github/repo-size/UserAccountNotFound/dbcs?style=flat)

# DBCS - Digital Business Card Service

Сервис цифровых визитных карточек с поддержкой QR-кодов, аналитики посещений и экспорта vCard.

![Linux](https://img.shields.io/badge/-Linux-6C6694.svg?logo=linux&style=flat)
![Python](https://img.shields.io/badge/-Python-F9DC3E.svg?logo=Python&style=flat)
![Vue.js](https://img.shields.io/badge/-Vue.js-4FC08D.svg?logo=vue.js&style=flat)
![FastAPI](https://img.shields.io/badge/-FastAPI-009688.svg?logo=fastapi&style=flat)

## 📋 Оглавление

- [Возможности](#-возможности)
- [Архитектура](#-архитектура)
- [Быстрый старт](#-быстрый-старт)
- [Конфигурация](#-конфигурация)
- [API Документация](#-api-документация)
- [Модели данных](#-модели-данных)
- [Безопасность](#-безопасность)
- [Развёртывание](#-развёртывание)
- [Структура проекта](#-структура-проекта)

## ✨ Возможности


### Для пользователей
- Создание и редактирование цифровых визиток
- Выбор шаблонов оформления
- Генерация QR-кодов для быстрого доступа
- Экспорт визитки в формате vCard (.vcf)
- Просмотр статистики посещений
- Загрузка аватаров и логотипов

### Для администраторов
- Управление пользователями
- Управление шаблонами визиток
- Общая аналитика системы
- Журнал аудита действий

### Технические особенности
- JWT аутентификация с refresh токенами
- HttpOnly cookies для безопасного хранения refresh токенов
- Ролевая модель (USER, ADMIN, SUPERADMIN)
- Логирование всех значимых действий
- REST API с автоматической документацией
- PWA (Progressive Web App) поддержка

## Архитектура

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Frontend      │────▶│     Backend      │────▶│   Database      │
│   Vue 3 + TS    │◀────│     FastAPI      │◀────│   MySQL/MariaDB │
│   Pinia + Axios │     │   SQLAlchemy     │     │                 │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

**Стек технологий:**

| Компонент | Технология |
|-----------|------------|
| Backend | Python 3.10+, FastAPI, SQLAlchemy 2.0 |
| Frontend | Vue 3, TypeScript, Pinia, Vue Router |
| Database | MySQL 8.0+ / MariaDB 10.5+ |
| Authentication | JWT (PyJWT), Argon2 для хеширования паролей |

## Быстрый старт

### Предварительные требования
- Python 3.10 или выше
- Node.js 18+ и npm
- MySQL 8.0+ или MariaDB 10.5+

### Backend
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
python create_SuperAdminUser.py
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Конфигурация

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| DATABASE_URL | URL подключения к БД | - |
| SECRET_KEY | Секретный ключ для JWT | - |
| ALLOWED_ORIGINS | Разрешённые CORS origin | "" |
| ACCESS_TOKEN_TTL_MINUTES | Время жизни access token | 15 |
| REFRESH_TOKEN_TTL_DAYS | Время жизни refresh token | 7 |

## API Документация

После запуска backend документация доступна по адресам:
- **Swagger UI:** http://localhost:8000/api/docs
- **ReDoc:** http://localhost:8000/api/redoc

### Основные эндпоинты

#### Аутентификация `/api/v1/auth`
| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| POST | `/register` | Регистрация |
| POST | `/login` | Вход |
| POST | `/refresh` | Обновление токена |
| GET | `/me` | Текущий пользователь |

#### Визитки `/api/v1/cards`
| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| GET | `/` | Список визиток |
| POST | `/` | Создание |
| GET | `/{id}` | Получение |
| PUT | `/{id}` | Обновление |
| DELETE | `/{id}` | Удаление |
| GET | `/{id}/qr` | QR код |
| GET | `/{id}/vcard` | Экспорт vCard |

## Модели данных

- **User**: Пользователь (email, password_hash, role)
- **Card**: Визитка (title, name, contact info, social links)
- **CardTemplate**: Шаблон визитки (name, config)
- **CardVisit**: Посещение (card_id, timestamp, ip_hash)
- **AuthSession**: Сессия аутентификации (user_id, refresh_token_hash)
- **AuditLog**: Журнал аудита (action, actor, entity)
- **File**: Файл (filename, mime_type, storage_path)

## Безопасность

- Access token: JWT, 15 минут, в памяти клиента
- Refresh token: HttpOnly cookie, 7 дней, ротация при использовании
- Пароли: Argon2id
- PII данные: SHA-256 с солью

## Развёртывание

```bash
# Backend
chmod +x ./deploy/deploy_backend.sh
./deploy/deploy_backend.sh

# Frontend
chmod +x ./deploy/deploy_frontend.sh
./deploy/deploy_frontend.sh
```

## Структура проекта

```
dbcs/
├── backend/
│   ├── app/
│   │   ├── api/              # API endpoints
│   │   ├── core/             # Конфигурация, безопасность
│   │   ├── db/               # Работа с БД
│   │   ├── models/           # SQLAlchemy модели
│   │   └── services/         # Бизнес-логика
│   └── README.md             # Документация backend
├── frontend/
│   └── src/
│       ├── api/              # API клиенты
│       ├── components/       # Vue компоненты
│       ├── stores/           # Pinia stores
│       └── views/            # Views/Pages
├── deploy/                   # Скрипты развёртывания
└── README.md                 # Этот файл
```
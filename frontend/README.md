# Документация к frontend

## Обзор

Frontend сервиса построен на **Vue 3** с использованием **TypeScript**, **Pinia** для управления состоянием и **Vite** для сборки.

## Стек технологий

- **Vue 3** - фреймворк
- **TypeScript** - типизация
- **Pinia** - state management
- **Vue Router** - маршрутизация
- **Axios** - HTTP клиент
- **TailwindCSS** - утилитарные CSS классы
- **Vite** - сборщик
- **vite-plugin-pwa** - PWA поддержка

## Структура проекта

```
frontend/
├── public/                     # Статические файлы
│   ├── favicon.ico
│   └── icons/                  # PWA иконки
├── src/
│   ├── App.vue                 # Корневой компонент
│   ├── main.ts                 # Точка входа
│   ├── api/                    # API клиенты
│   │   ├── client.ts           # Axios инстанс
│   │   ├── auth.ts             # Auth API
│   │   ├── cards.ts            # Cards API
│   │   ├── publicCards.ts      # Public Cards API
│   │   ├── templates.ts        # Templates API
│   │   ├── files.ts            # Files API
│   │   └── admin.ts            # Admin API
│   ├── components/             # Vue компоненты
│   │   ├── common/             # Общие компоненты
│   │   ├── card/               # Компоненты визиток
│   │   ├── form/               # Формы
│   │   └── admin/              # Админские компоненты
│   ├── layouts/                # Layouts
│   │   ├── DefaultLayout.vue
│   │   └── AdminLayout.vue
│   ├── router/                 # Маршруты
│   │   └── index.ts
│   ├── stores/                 # Pinia stores
│   │   ├── auth.ts             # Auth store
│   │   └── cards.ts            # Cards store
│   ├── types/                  # TypeScript типы
│   │   ├── card.ts
│   │   ├── user.ts
│   │   ├── template.ts
│   │   ├── analytics.ts
│   │   ├── stats.ts
│   │   ├── admin.ts
│   │   └── publicCard.ts
│   ├── utils/                  # Утилиты
│   │   ├── download.ts         # Скачивание файлов
│   │   └── ...
│   ├── views/                  # Views/Pages
│   │   ├── LoginView.vue       # Страница входа
│   │   ├── DashboardView.vue   # Дашборд
│   │   ├── CardEditView.vue    # Редактирование визитки
│   │   ├── PublicCardView.vue  # Публичная визитка
│   │   └── admin/              # Админские страницы
│   │       ├── AdminDashboardView.vue
│   │       ├── AdminUsersView.vue
│   │       ├── AdminCardsView.vue
│   │       ├── AdminTemplatesView.vue
│   │       ├── AdminAuditView.vue
│   │       └── AdminAnalyticsView.vue
│   └── assets/                 # Ассеты (images, styles)
├── index.html                  # HTML шаблон
├── package.json                # Зависимости
├── vite.config.ts              # Vite конфиг
├── tailwind.config.js          # Tailwind конфиг
├── postcss.config.js           # PostCSS конфиг
├── tsconfig.json               # TypeScript конфиг
└── README.md                   # Этот файл
```

## Установка

### Требования

- Node.js 18+
- npm 9+

### Шаги установки

```bash
# Установка зависимостей
npm install

# Копирование примера окружения
cp .env.example .env

# Редактирование .env
nano .env
```

## Конфигурация

Переменные окружения в `.env`:

```env
# API Base URL
VITE_API_BASE_URL=http://localhost:8000/api/v1

# App Title
VITE_APP_TITLE=DBCS - Digital Business Card Service

# PWA Configuration
VITE_PWA_ENABLED=true
```

## Запуск

### Development

```bash
npm run dev
```

Приложение будет доступно по адресу: http://localhost:5173

### Production build

```bash
npm run build
```

Собранные файлы будут в директории `dist/`.

### Preview production build

```bash
npm run preview
```

## Скрипты

| Скрипт | Описание |
|--------|----------|
| `npm run dev` | Запуск dev сервера |
| `npm run build` | Сборка для продакшена |
| `npm run preview` | Preview production сборки |
| `npm run type-check` | Проверка типов TypeScript |

## Архитектура

### State Management (Pinia)

#### Auth Store
Управляет состоянием аутентификации:
- `user`: текущий пользователь
- `accessToken`: JWT токен
- `isAuthenticated`: статус аутентификации
- `login()`: вход
- `logout()`: выход
- `refreshToken()`: обновление токена
- `fetchUser()`: получение данных пользователя

#### Cards Store
Управляет визитками:
- `cards`: список визиток
- `currentCard`: текущая редактируемая визитка
- `fetchCards()`: получение списка
- `createCard()`: создание
- `updateCard()`: обновление
- `deleteCard()`: удаление

### API Client

Axios настроен с интерцепторами для:
- Автоматической подстановки access token
- Silent refresh при истечении токена
- Обработки ошибок авторизации

```typescript
// src/api/client.ts
import axios from 'axios';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Для refresh cookie
});

// Interceptor для добавления токена
apiClient.interceptors.request.use((config) => {
  const token = useAuthStore().accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Interceptor для обработки ошибок
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Попытка refresh токена
      await refreshAccessToken();
    }
    return Promise.reject(error);
  }
);
```

### Роутинг

Маршруты защищены guards для проверки аутентификации:

```typescript
// Защищённые маршруты
{
  path: '/dashboard',
  component: DashboardView,
  meta: { requiresAuth: true }
}

// Админские маршруты
{
  path: '/admin',
  component: AdminLayout,
  meta: { requiresAuth: true, requiresAdmin: true }
}
```

### Компоненты

#### Базовая структура компонента

```vue
<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useAuthStore } from '@/stores/auth';
import type { Card } from '@/types/card';

// Props
interface Props {
  cardId?: string;
}
const props = defineProps<Props>();

// Emits
const emit = defineEmits<{
  (e: 'updated', card: Card): void;
}>();

// State
const loading = ref(false);
const error = ref<string | null>(null);

// Computed
const isValid = computed(() => {
  // validation logic
});

// Methods
async function fetchData() {
  loading.value = true;
  try {
    // fetch data
  } catch (err) {
    error.value = 'Failed to load data';
  } finally {
    loading.value = false;
  }
}

// Lifecycle
onMounted(() => {
  fetchData();
});
</script>

<template>
  <div>
    <div v-if="loading">Loading...</div>
    <div v-else-if="error">{{ error }}</div>
    <div v-else>
      <!-- Content -->
    </div>
  </div>
</template>
```

## Типы данных

### User
```typescript
export interface User {
  id: string;
  email: string;
  full_name: string;
  role: 'USER' | 'ADMIN' | 'SUPERADMIN';
  is_active: boolean;
  created_at: string;
  updated_at: string;
  last_login_at: string | null;
}
```

### Card
```typescript
export interface Card {
  id: string;
  user_id: string;
  template_id: string;
  public_id: string;
  title: string;
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  company: string;
  position: string;
  website: string;
  address: string;
  bio: string;
  avatar_file_id: string | null;
  logo_file_id: string | null;
  social_links: Record<string, string>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}
```

### AuthResponse
```typescript
export interface AuthResponse {
  access_token: string;
  token_type: 'bearer';
  expires_in: number;
  user: User;
}
```

## PWA (Progressive Web App)

Приложение поддерживает установку как PWA:

- Offline режим
- Установка на домашний экран

Конфигурация в `vite.config.ts`:

```typescript
import { VitePWA } from 'vite-plugin-pwa';

export default defineConfig({
  plugins: [
    vue(),
    VitePWA({
      registerType: 'autoUpdate',
      manifest: {
        name: 'DBCS - Digital Business Card Service',
        short_name: 'DBCS',
        description: 'Сервис цифровых визитных карточек',
        theme_color: '#ffffff',
        background_color: '#ffffff',
        display: 'standalone',
        icons: [
          {
            src: '/icons/icon-192x192.png',
            sizes: '192x192',
            type: 'image/png'
          },
          {
            src: '/icons/icon-512x512.png',
            sizes: '512x512',
            type: 'image/png'
          }
        ]
      }
    })
  ]
});
```

## Стилизация

Используется TailwindCSS:

```javascript
// tailwind.config.js
module.exports = {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          500: '#3b82f6',
          600: '#2563eb',
        }
      }
    }
  },
  plugins: []
}
```

## Best Practices

### Компоненты
- Использовать Composition API (`<script setup>`)
- Типизировать props и emits
- Разделять компоненты на логические части
- Избегать прямой мутации props

### State Management
- Хранить в Pinia только глобальное состояние
- Локальное состояние хранить в компонентах
- Использовать getters для вычисляемых значений

### API
- Всегда обрабатывать ошибки
- Показывать loading состояния
- Использовать TypeScript типы для ответов API

### Производительность
- Ленивая загрузка routes
- Оптимизация изображений
- Кэширование API запросов

## Тестирование

```bash
# Unit тесты (будущая функциональность)
npm run test:unit

# E2E тесты
npm run test:e2e
```

## Линтинг

```bash
# Проверка типов
npm run type-check

# ESLint (будущая функциональность)
npm run lint
```

## Развёртывание

См. скрипт `../deploy/deploy_frontend.sh`

### Production чеклист

- [ ] VITE_API_BASE_URL настроен
- [ ] Сборка прошла без ошибок
- [ ] PWA иконки присутствуют
- [ ] HTTPS настроен
- [ ] Caching настроен
- [ ] Source maps отключены (опционально)


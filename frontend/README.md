# Документация frontend

Frontend DBCS: **Vue 3** + **TypeScript** + **Pinia** + **Vue Router** + **vue-i18n** + **Vite** + **TailwindCSS** + **PWA**.

Версия пакета: см. `package.json` (сейчас `1.4.5`).

## Стек

| Библиотека | Назначение |
|------------|------------|
| Vue 3 | UI |
| TypeScript | Типы |
| Pinia | Auth store |
| Vue Router | Маршруты + guards |
| vue-i18n | RU / EN |
| Axios | HTTP (`withCredentials` для refresh cookie) |
| TailwindCSS | Стили |
| Vite + vite-plugin-pwa | Сборка и PWA |

## Структура

```
frontend/
├── public/                     # favicon, PWA-иконки
├── src/
│   ├── main.ts
│   ├── App.vue
│   ├── style.css
│   ├── api/
│   │   ├── client.ts           # Axios + silent refresh
│   │   ├── cards.ts
│   │   ├── publicCards.ts
│   │   ├── templates.ts
│   │   ├── files.ts
│   │   ├── admin.ts
│   │   └── system.ts
│   ├── components/
│   │   ├── admin/              # UserFormModal, TemplateCreateModal
│   │   ├── analytics/          # Charts, PeriodSelector
│   │   ├── cards/              # CardForm, TemplateSelector, …
│   │   ├── common/             # LanguageSwitcher
│   │   ├── public/             # PublicCardRenderer, PolygonNetworkBackground
│   │   └── pwa/                # InstallPrompt
│   ├── composables/
│   │   └── useLocaleDate.ts
│   ├── i18n/
│   │   ├── index.ts
│   │   └── locales/            # ru.ts, en.ts
│   ├── layouts/
│   │   └── AdminLayout.vue
│   ├── router/index.ts
│   ├── stores/auth.ts          # Единственный Pinia store
│   ├── types/
│   ├── utils/                  # apiError, download, messengerLinks, …
│   └── views/
│       ├── LoginView.vue
│       ├── DashboardView.vue
│       ├── CardEditView.vue
│       ├── PublicCardView.vue
│       └── admin/
│           ├── AdminDashboardView.vue
│           ├── AdminUsersView.vue
│           ├── AdminCardsView.vue
│           ├── AdminTemplatesView.vue
│           ├── AdminAuditView.vue
│           ├── AdminBackupView.vue
│           └── AdminSettingsView.vue
├── additional_scripts/
│   └── deploy_frontend.sh
├── .env.example
├── package.json
├── vite.config.ts
├── tailwind.config.js
└── README.md
```

## Установка

```bash
cd frontend
npm install
cp .env.example .env
```

Требования: Node.js 18+, npm 9+.

## Конфигурация

```env
# Относительный путь: в dev — Vite proxy /api → http://127.0.0.1:8000
# в prod — тот же путь за nginx
VITE_API_BASE_URL=/api/v1
```

Версия приложения пробрасывается из `package.json` как `import.meta.env.VITE_APP_VERSION`.

Локаль UI: `localStorage` ключ `dbcs-locale` (`ru` | `en`), по умолчанию `ru`.

> В строках i18n символ `@` нужно экранировать как `{'@'}`, иначе vue-i18n парсит linked-message и падает (например, плейсхолдер Telegram).

## Скрипты

| Команда | Описание |
|---------|----------|
| `npm run dev` | Dev-сервер (http://localhost:5173) |
| `npm run build` | `vue-tsc -b` + production build → `dist/` |
| `npm run preview` | Preview сборки |

Отдельного `type-check` / `lint` скрипта в `package.json` нет — проверка типов входит в `build`.

## Маршруты

| Path | Имя | Доступ |
|------|-----|--------|
| `/login` | login | гость |
| `/` | dashboard | auth |
| `/cards/new` | card-new | auth |
| `/cards/:id` | card-edit | auth |
| `/public/card/:slug` | public-card | публично |
| `/admin` | admin-dashboard | admin+ |
| `/admin/users`, `/cards`, `/templates`, `/audit` | … | admin+ |
| `/admin/backup`, `/admin/settings` | … | SuperAdmin |

Guards в `router/index.ts`: `requiresAuth`, `requiresGuest`, `requiresAdmin`, `requiresSuperAdmin`.

## Состояние и API

### Auth store (`stores/auth.ts`)
- `user`, `accessToken`, `isAuthenticated`, `isAdmin`
- `login`, `fetchMe`, `logout` / `forceLogout`
- Access token в `localStorage`; refresh — HttpOnly cookie через `withCredentials`

Отдельного Pinia store для визиток нет: списки и формы ходят в `cardApi` / локальный state во views.

### Axios (`api/client.ts`)
- Подставляет `Authorization: Bearer …`
- При 401 — один concurrent `/auth/refresh`, очередь повторов, иначе logout

### Типы визитки (актуально)

```typescript
// упрощённо — см. src/types/card.ts
interface Card {
  id: string;
  slug: string;
  title: string;
  full_name: string;
  // … job_title, department, company, phones, messengers, email, website, …
  theme: CardTheme;
  template_id: string | null;
  avatar_file_id: string | null;
  logo_file_id: string | null;
  is_active: boolean;
  public_url: string;
  // …
}
```

Публичный рендер: `PublicCardRenderer` + CSS шаблона с backend (`/api/v1/templates/{code}/css`). Безопасные ссылки: `utils/messengerLinks.ts` (`safeWebsiteHref`, allowlist схем).

## PWA

`vite-plugin-pwa`: `registerType: 'autoUpdate'`, precache статики, `navigateFallback` на `index.html` (API не перехватывается как навигация), runtime cache для списка визиток и публичных карточек. Иконки: `pwa-192x192.png`, `pwa-512x512.png`.

## Развёртывание

```bash
sudo bash additional_scripts/deploy_frontend.sh
```

Сборка → `/var/www/dbcs/frontend`, настройка nginx (в т.ч. TLS из `/opt/dbcs/.tls.env`).

### Production чеклист
- [ ] `VITE_API_BASE_URL` указывает на `/api/v1` (или корректный origin)
- [ ] `npm run build` без ошибок
- [ ] HTTPS
- [ ] После деплоя при странном UI — hard refresh / сброс service worker

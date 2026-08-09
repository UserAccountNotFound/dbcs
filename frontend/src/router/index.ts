import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '../stores/auth';

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue'),
      meta: { requiresGuest: true }
    },
    {
      path: '/',
      name: 'dashboard',
      component: () => import('../views/DashboardView.vue'),
      meta: { requiresAuth: true }
    },
    {
      // этот маршрут должен быть ДО /cards/:id,
      // иначе Vue Router думает, что "new" — это id карточки
      path: '/cards/new',
      name: 'card-new',
      component: () => import('../views/CardEditView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/cards/:id',
      name: 'card-edit',
      component: () => import('../views/CardEditView.vue'),
      meta: { requiresAuth: true }
    },
    {
      // Публичная визитка (без авторизации)
      path: '/public/card/:slug',
      name: 'public-card',
      component: () => import('../views/PublicCardView.vue')
    },
    {
      path: '/admin',
      component: () => import('../layouts/AdminLayout.vue'),
      meta: { requiresAuth: true, requiresAdmin: true },
      children: [
        {
          path: '',
          name: 'admin-dashboard',
          component: () => import('../views/admin/AdminDashboardView.vue'),
        },
        {
          path: 'users',
          name: 'admin-users',
          component: () => import('../views/admin/AdminUsersView.vue'),
        },
        {
          path: 'cards',
          name: 'admin-cards',
          component: () => import('../views/admin/AdminCardsView.vue'),
        },
        {
          path: 'templates',
          name: 'admin-templates',
          component: () => import('../views/admin/AdminTemplatesView.vue'),
        },
        {
          path: 'audit',
          name: 'admin-audit',
          component: () => import('../views/admin/AdminAuditView.vue'),
        },
        {
          // Старый путь: обзор и аналитика объединены на /admin
          path: 'analytics',
          redirect: { name: 'admin-dashboard' },
        },
      ],
    },
  ]
});

router.beforeEach(async (to, _from, next) => {
  const authStore = useAuthStore();

  // Если есть токен в localStorage, но нет юзера в стейте (например, после F5)
  if (authStore.accessToken && !authStore.user) {
    await authStore.fetchMe();
  }

  // Защита маршрутов, требующих авторизации
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next({ name: 'login' });
  } 
  // Защита маршрутов для гостей (если уже залогинен — редирект на дашборд)
  else if (to.meta.requiresGuest && authStore.isAuthenticated) {
    next({ name: 'dashboard' });
  } 
  // Доступность только для админов
  else if (to.meta.requiresAdmin && !authStore.isAdmin) {
    next({ name: 'dashboard' });
  } 
  else {
    next();
  }
});

export default router;
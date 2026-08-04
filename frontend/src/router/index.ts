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
      path: '/cards/:id',
      name: 'card-edit',
      component: () => import('../views/CardEditView.vue'),
      meta: { requiresAuth: true }
    },
    {
      // Публичная визитка (отдельный layout, без авторизации)
      path: '/public/card/:slug',
      name: 'public-card',
      component: () => import('../views/PublicCardView.vue')
    }
  ]
});

router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore();

  // Если есть токен в localStorage, но нет юзера в стейте (например, после F5)
  if (authStore.accessToken && !authStore.user) {
    await authStore.fetchMe();
  }

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next({ name: 'login' });
  } else if (to.meta.requiresGuest && authStore.isAuthenticated) {
    next({ name: 'dashboard' });
  } else {
    next();
  }
});

export default router;
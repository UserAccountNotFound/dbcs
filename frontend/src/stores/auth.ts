import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import apiClient from '../api/client';

interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
  is_active?: boolean;
  mfa_enabled?: boolean;
  created_at?: string;
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null);
  const accessToken = ref<string | null>(localStorage.getItem('access_token'));

  const isAuthenticated = computed(() => !!accessToken.value && !!user.value);

  function setAccessToken(token: string | null) {
    accessToken.value = token;
    if (token) {
      localStorage.setItem('access_token', token);
    } else {
      localStorage.removeItem('access_token');
    }
  }

  async function login(email: string, password: string) {
    const { data } = await apiClient.post('/auth/login', { email, password });
    setAccessToken(data.access_token);
    user.value = data.user;
  }

  async function fetchMe() {
    if (!accessToken.value) return;
    try {
      const { data } = await apiClient.get('/auth/me');
      user.value = data;
    } catch (e: unknown) {
      const status = (e as { response?: { status?: number } })?.response?.status;
      if (status === 401 || status === 403) {
        await forceLogout({ callApi: false });
      }
      // сеть / 5xx — не сбрасываем сессию
    }
  }

  async function clearCaches() {
    if ('caches' in window) {
      try {
        const cacheNames = await caches.keys();
        await Promise.all(
          cacheNames
            .filter(
              (name) =>
                name.includes('user-cards') ||
                name.includes('public-cards') ||
                name.includes('images')
            )
            .map((name) => caches.delete(name))
        );
      } catch (e) {
        console.error('Cache cleanup error:', e);
      }
    }
  }

  async function forceLogout(options: { callApi?: boolean } = {}) {
    const { callApi = true } = options;

    if (callApi) {
      try {
        await apiClient.post('/auth/logout');
      } catch {
        // Игнорируем ошибки сети при логауте
      }
    }

    await clearCaches();
    setAccessToken(null);
    user.value = null;

    const { default: router } = await import('../router');
    if (router.currentRoute.value.path !== '/login') {
      await router.push('/login');
    }
  }

  async function logout() {
    await forceLogout({ callApi: true });
  }

  const isAdmin = computed(
    () => user.value?.role === 'ADMIN' || user.value?.role === 'SUPERADMIN'
  );

  return {
    user,
    accessToken,
    isAuthenticated,
    isAdmin,
    setAccessToken,
    login,
    fetchMe,
    logout,
    forceLogout,
  };
});

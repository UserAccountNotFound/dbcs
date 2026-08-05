import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import apiClient from '../api/client';
import router from '../router';

interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null);
  const accessToken = ref<string | null>(localStorage.getItem('access_token'));

  const isAuthenticated = computed(() => !!accessToken.value && !!user.value);

  async function login(email: string, password: string) {
    const { data } = await apiClient.post('/auth/login', { email, password });
    accessToken.value = data.access_token;
    user.value = data.user;
    localStorage.setItem('access_token', data.access_token);
  }

  async function fetchMe() {
    if (!accessToken.value) return;
    try {
      const { data } = await apiClient.get('/auth/me');
      user.value = data;
    } catch (e) {
      logout();
    }
  }

  async function clearCaches() {
    if ('caches' in window) {
      try {
        const cacheNames = await caches.keys();
        await Promise.all(
          cacheNames
            .filter(name => 
              name.includes('user-cards') || 
              name.includes('public-cards') ||
              name.includes('images')
            )
            .map(name => caches.delete(name))
        );
      } catch (e) {
        console.error('Cache cleanup error:', e);
      }
    }
  }

  async function logout() {
    try {
      await apiClient.post('/auth/logout');
    } catch {
      // Игнорируем ошибки сети при логауте
    } finally {
      // Очищаем кэшированные данные перед выходом
      await clearCaches();
      
      accessToken.value = null;
      user.value = null;
      localStorage.removeItem('access_token');
      router.push('/login');
    }
  }

  const isAdmin = computed(() => 
    user.value?.role === 'ADMIN' || user.value?.role === 'SUPERADMIN'
  );

  return { user, accessToken, isAuthenticated, isAdmin, login, fetchMe, logout };
});
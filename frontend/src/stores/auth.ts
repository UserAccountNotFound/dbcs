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

  async function logout() {
    try {
      await apiClient.post('/auth/logout');
    } catch (e) {
      // Игнорируем ошибки при логауте
    } finally {
      accessToken.value = null;
      user.value = null;
      localStorage.removeItem('access_token');
      router.push('/login');
    }
  }

  return { user, accessToken, isAuthenticated, login, fetchMe, logout };
});
<script setup lang="ts">
import { useAuthStore } from '../stores/auth';

const authStore = useAuthStore();

const menuItems = [
  { name: 'admin-dashboard', label: 'Обзор', icon: '📊' },
  { name: 'admin-users', label: 'Пользователи', icon: '👥' },
  { name: 'admin-cards', label: 'Визитки', icon: '💳' },
  { name: 'admin-templates', label: 'Шаблоны', icon: '🎨' },
  { name: 'admin-audit', label: 'Аудит', icon: '📋' },
];
</script>

<template>
  <div class="min-h-screen bg-gray-100 flex">
    <!-- Боковое меню -->
    <aside class="w-64 bg-gray-900 text-white flex flex-col">
      <div class="p-6 border-b border-gray-800">
        <h1 class="text-xl font-bold">DBCS Admin</h1>
        <p class="text-gray-400 text-sm mt-1">{{ authStore.user?.email }}</p>
      </div>

      <nav class="flex-1 p-4 space-y-1">
        <router-link 
          v-for="item in menuItems" 
          :key="item.name"
          :to="{ name: item.name }"
          class="flex items-center gap-3 px-4 py-3 rounded-lg transition-colors"
          :class="$route.name === item.name ? 'bg-primary text-white' : 'text-gray-300 hover:bg-gray-800'"
        >
          <span>{{ item.icon }}</span>
          <span>{{ item.label }}</span>
        </router-link>
      </nav>

      <div class="p-4 border-t border-gray-800">
        <router-link to="/" class="block px-4 py-2 text-gray-300 hover:text-white transition-colors">
          ← Личный кабинет
        </router-link>
        <button @click="authStore.logout()" class="w-full mt-2 px-4 py-2 text-left text-red-400 hover:text-red-300 transition-colors">
          Выйти
        </button>
      </div>
    </aside>

    <!-- Основной контент -->
    <main class="flex-1 p-8 overflow-auto">
      <router-view />
    </main>
  </div>
</template>
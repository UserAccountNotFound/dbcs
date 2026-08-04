<script setup lang="ts">
import { useAuthStore } from '../stores/auth';

const authStore = useAuthStore();
</script>

<template>
  <div class="min-h-screen bg-gray-50">
    <header class="bg-white shadow">
      <div class="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8 flex justify-between items-center">
        <h1 class="text-3xl font-bold text-gray-900">Мои визитки</h1>
        <div class="flex items-center gap-4">
          <span class="text-gray-600">{{ authStore.user?.full_name }}</span>
          <button @click="authStore.logout()" class="text-sm text-red-600 hover:text-red-800 font-medium">
            Выйти
          </button>
        </div>
      </div>
    </header>
    
    <main class="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
      <div class="px-4 py-6 sm:px-0">
        <div class="border-4 border-dashed border-gray-200 rounded-lg h-96 flex items-center justify-center text-gray-500">
          Здесь будет список визиток и кнопка "Создать новую"
        </div>
      </div>
    </main>
  </div>
</template>
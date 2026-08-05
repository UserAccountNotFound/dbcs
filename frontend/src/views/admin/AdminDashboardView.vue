<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { adminApi } from '../../api/admin';
import type { OverviewStats } from '../../types/admin';

const stats = ref<OverviewStats | null>(null);
const isLoading = ref(true);

onMounted(async () => {
  try {
    stats.value = await adminApi.getOverviewStats();
  } catch (e) {
    console.error('Failed to load stats', e);
  } finally {
    isLoading.value = false;
  }
});

const cards = [
  { key: 'total_users', label: 'Всего пользователей', color: 'bg-blue-500' },
  { key: 'active_users', label: 'Активных пользователей', color: 'bg-green-500' },
  { key: 'total_cards', label: 'Всего визиток', color: 'bg-purple-500' },
  { key: 'active_cards', label: 'Активных визиток', color: 'bg-teal-500' },
  { key: 'total_visits', label: 'Всего просмотров', color: 'bg-orange-500' },
  { key: 'total_vcard_downloads', label: 'Скачиваний vCard', color: 'bg-pink-500' },
];
</script>

<template>
  <div>
    <h2 class="text-2xl font-bold text-gray-900 mb-6">Обзор системы</h2>

    <div v-if="isLoading" class="flex justify-center py-12">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
    </div>

    <div v-else-if="stats" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <div 
        v-for="card in cards" 
        :key="card.key"
        class="bg-white rounded-xl shadow-sm p-6 border border-gray-100"
      >
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-gray-500">{{ card.label }}</p>
            <p class="text-3xl font-bold mt-2 text-gray-900">
              {{ stats[card.key as keyof OverviewStats] }}
            </p>
          </div>
          <div :class="card.color" class="w-12 h-12 rounded-lg opacity-20"></div>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { adminApi } from '../../api/admin';
import type { AdminCard } from '../../types/admin';
import { getAxiosErrorMessage } from '../../utils/apiError';

const cards = ref<AdminCard[]>([]);
const total = ref(0);
const limit = ref(20);
const offset = ref(0);
const search = ref('');
const isLoading = ref(true);
const searchTimeout = ref<number>();

async function loadCards() {
  isLoading.value = true;
  try {
    const response = await adminApi.getCards(limit.value, offset.value, search.value);
    cards.value = response.items;
    total.value = response.total;
  } catch (e) {
    console.error('Failed to load cards', e);
  } finally {
    isLoading.value = false;
  }
}

onMounted(loadCards);

watch(search, () => {
  clearTimeout(searchTimeout.value);
  searchTimeout.value = window.setTimeout(() => {
    offset.value = 0;
    loadCards();
  }, 500);
});

async function deactivateCard(card: AdminCard) {
  if (!confirm(`Отключить визитку "${card.title}"?`)) return;
  
  try {
    await adminApi.deactivateCard(card.id);
    card.is_active = false;
  } catch (e: unknown) {
    alert(getAxiosErrorMessage(e, 'Ошибка при деактивации'));
  }
}

// ИСПРАВЛЕНО: используем computed вместо функций
const totalPages = computed(() => Math.ceil(total.value / limit.value));
const currentPage = computed(() => Math.floor(offset.value / limit.value) + 1);

function nextPage() {
  if (currentPage.value < totalPages.value) {
    offset.value += limit.value;
    loadCards();
  }
}

function prevPage() {
  if (currentPage.value > 1) {
    offset.value -= limit.value;
    loadCards();
  }
}
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <h2 class="text-2xl font-bold text-gray-900">Визитки</h2>
      <input 
        v-model="search"
        type="text"
        placeholder="Поиск по названию, имени или slug..."
        class="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary w-64"
      />
    </div>

    <div class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
      <table class="w-full">
        <thead class="bg-gray-50 border-b border-gray-100">
          <tr>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Визитка</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Владелец</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Просмотры</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Статус</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Действия</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-100">
          <tr v-if="isLoading">
            <td colspan="5" class="px-6 py-12 text-center text-gray-500">Загрузка...</td>
          </tr>
          <tr v-else-if="cards.length === 0">
            <td colspan="5" class="px-6 py-12 text-center text-gray-500">Визитки не найдены</td>
          </tr>
          <tr v-for="card in cards" :key="card.id" class="hover:bg-gray-50">
            <td class="px-6 py-4">
              <div class="font-medium text-gray-900">{{ card.title }}</div>
              <div class="text-sm text-gray-500">{{ card.full_name }} • {{ card.slug }}</div>
            </td>
            <td class="px-6 py-4 text-sm text-gray-600">{{ card.user_email }}</td>
            <td class="px-6 py-4 text-gray-600">{{ card.visits_count }}</td>
            <td class="px-6 py-4">
              <span 
                :class="[
                  'px-2 py-1 rounded-full text-xs font-medium',
                  card.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                ]"
              >
                {{ card.is_active ? 'Активна' : 'Отключена' }}
              </span>
            </td>
            <td class="px-6 py-4">
              <button 
                v-if="card.is_active"
                @click="deactivateCard(card)"
                class="text-sm text-red-600 hover:bg-red-50 px-3 py-1 rounded transition-colors"
              >
                Отключить
              </button>
              <span v-else class="text-sm text-gray-400">—</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Пагинация -->
    <div class="flex justify-between items-center mt-4">
      <p class="text-sm text-gray-500">
        Всего: {{ total }} | Страница {{ currentPage }} из {{ totalPages }}
      </p>
      <div class="flex gap-2">
        <button @click="prevPage" :disabled="currentPage === 1" class="btn-secondary disabled:opacity-50">← Назад</button>
        <button @click="nextPage" :disabled="currentPage === totalPages" class="btn-secondary disabled:opacity-50">Вперед →</button>
      </div>
    </div>
  </div>
</template>
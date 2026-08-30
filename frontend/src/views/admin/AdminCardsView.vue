<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { adminApi } from '../../api/admin';
import type { AdminCard } from '../../types/admin';
import { getAxiosErrorMessage } from '../../utils/apiError';

const { t } = useI18n();

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
  if (!confirm(t('cards.deactivateConfirm', { title: card.title }))) return;

  try {
    await adminApi.deactivateCard(card.id);
    card.is_active = false;
  } catch (e: unknown) {
    alert(getAxiosErrorMessage(e, t('errors.deactivateFailed')));
  }
}

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
      <h2 class="text-2xl font-bold text-gray-900">{{ t('admin.cards') }}</h2>
      <input
        v-model="search"
        type="text"
        :placeholder="t('cards.searchPlaceholder')"
        class="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary w-64"
      />
    </div>

    <div class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
      <table class="w-full">
        <thead class="bg-gray-50 border-b border-gray-100">
          <tr>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{{ t('cards.columnCard') }}</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{{ t('cards.columnOwner') }}</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{{ t('cards.columnViews') }}</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{{ t('cards.columnStatus') }}</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{{ t('cards.columnActions') }}</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-100">
          <tr v-if="isLoading">
            <td colspan="5" class="px-6 py-12 text-center text-gray-500">{{ t('common.loadingShort') }}</td>
          </tr>
          <tr v-else-if="cards.length === 0">
            <td colspan="5" class="px-6 py-12 text-center text-gray-500">{{ t('cards.notFound') }}</td>
          </tr>
          <tr v-for="card in cards" :key="card.id" class="hover:bg-gray-50">
            <td class="px-6 py-4">
              <div class="font-medium text-gray-900">{{ card.title }}</div>
              <div class="text-sm text-gray-500">
                {{ card.full_name }} •
                <router-link
                  :to="`/public/card/${card.slug}`"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="font-mono text-primary hover:text-teal-800 hover:underline"
                  :title="t('cards.openPublic', { slug: card.slug })"
                  @click.stop
                >
                  {{ card.slug }}
                </router-link>
              </div>
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
                {{ card.is_active ? t('common.active') : t('common.inactive') }}
              </span>
            </td>
            <td class="px-6 py-4">
              <button
                v-if="card.is_active"
                @click="deactivateCard(card)"
                class="text-sm text-red-600 hover:bg-red-50 px-3 py-1 rounded transition-colors"
              >
                {{ t('common.disable') }}
              </button>
              <span v-else class="text-sm text-gray-400">{{ t('common.dash') }}</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="flex justify-between items-center mt-4">
      <p class="text-sm text-gray-500">
        {{ t('common.total') }}: {{ total }} | {{ t('common.page') }} {{ currentPage }} {{ t('common.of') }} {{ totalPages }}
      </p>
      <div class="flex gap-2">
        <button @click="prevPage" :disabled="currentPage === 1" class="btn-secondary disabled:opacity-50">{{ t('common.back') }}</button>
        <button @click="nextPage" :disabled="currentPage === totalPages" class="btn-secondary disabled:opacity-50">{{ t('common.forward') }}</button>
      </div>
    </div>
  </div>
</template>

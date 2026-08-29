<script setup lang="ts">
import { ref, watch, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { cardApi } from '../../api/cards';
import type { CardStats } from '../../types/stats';
import { useLocaleDate } from '../../composables/useLocaleDate';

const { t } = useI18n();
const { formatDate } = useLocaleDate();

const props = defineProps<{ 
  cardId: string | null; 
  cardTitle?: string;
}>();

const emit = defineEmits(['close']);

const stats = ref<CardStats | null>(null);
const isLoading = ref(false);
const error = ref('');
let requestId = 0;

watch(() => props.cardId, async (newId) => {
  const currentRequest = ++requestId;

  if (newId) {
    isLoading.value = true;
    error.value = '';
    stats.value = null;
    
    try {
      const result = await cardApi.getCardStats(newId);
      if (currentRequest !== requestId || props.cardId !== newId) {
        return;
      }
      stats.value = result;
    } catch (e) {
      if (currentRequest !== requestId) return;
      error.value = t('errors.statsLoad');
    } finally {
      if (currentRequest === requestId) {
        isLoading.value = false;
      }
    }
  } else {
    stats.value = null;
  }
}, { immediate: true });

const maxDailyValue = computed(() => {
  if (!stats.value || stats.value.daily.length === 0) return 1;
  return Math.max(
    ...stats.value.daily.map(d => d.views + d.vcard_downloads), 
    1
  );
});
</script>

<template>
  <div v-if="cardId" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" @click.self="$emit('close')">
    <div class="bg-white rounded-2xl p-6 max-w-2xl w-full shadow-2xl max-h-[90vh] overflow-y-auto">
      <div class="flex justify-between items-start mb-6">
        <div>
          <h3 class="text-xl font-bold text-gray-900">{{ t('cards.statsTitle') }}</h3>
          <p v-if="cardTitle" class="text-gray-500 text-sm mt-1">{{ cardTitle }}</p>
        </div>
        <button @click="$emit('close')" class="text-gray-400 hover:text-gray-600 text-2xl leading-none">&times;</button>
      </div>

      <div v-if="isLoading" class="flex justify-center py-12">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>

      <div v-else-if="error" class="text-center py-8 text-red-600">
        {{ error }}
      </div>

      <div v-else-if="stats">
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <div class="bg-gray-50 rounded-xl p-4 text-center">
            <div class="text-2xl font-bold text-gray-900">{{ stats.total_views }}</div>
            <div class="text-xs text-gray-500 mt-1">{{ t('cards.totalViews') }}</div>
          </div>
          <div class="bg-gray-50 rounded-xl p-4 text-center">
            <div class="text-2xl font-bold text-gray-900">{{ stats.total_vcard_downloads }}</div>
            <div class="text-xs text-gray-500 mt-1">{{ t('cards.totalDownloads') }}</div>
          </div>
          <div class="bg-blue-50 rounded-xl p-4 text-center">
            <div class="text-2xl font-bold text-blue-700">{{ stats.views_last_30_days }}</div>
            <div class="text-xs text-blue-600 mt-1">{{ t('cards.views30d') }}</div>
          </div>
          <div class="bg-green-50 rounded-xl p-4 text-center">
            <div class="text-2xl font-bold text-green-700">{{ stats.vcard_downloads_last_30_days }}</div>
            <div class="text-xs text-green-600 mt-1">{{ t('cards.downloads30d') }}</div>
          </div>
        </div>

        <div class="mb-2 flex justify-between items-center">
          <h4 class="font-semibold text-gray-800">{{ t('cards.activity30d') }}</h4>
          <div class="flex gap-4 text-xs">
            <span class="flex items-center gap-1">
              <span class="w-3 h-3 rounded-sm bg-primary inline-block"></span> {{ t('cards.views') }}
            </span>
            <span class="flex items-center gap-1">
              <span class="w-3 h-3 rounded-sm bg-green-500 inline-block"></span> {{ t('cards.vcard') }}
            </span>
          </div>
        </div>

        <div class="h-48 flex items-end gap-[2px] border-b border-gray-100 pb-1">
          <div 
            v-for="day in stats.daily" 
            :key="day.date" 
            class="flex-1 flex flex-col justify-end h-full group relative cursor-pointer"
          >
            <div class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block bg-gray-900 text-white text-xs rounded-lg px-3 py-2 whitespace-nowrap z-10 shadow-lg pointer-events-none">
              <div class="font-semibold mb-1">{{ formatDate(day.date) }}</div>
              <div class="flex items-center gap-2">
                <span class="w-2 h-2 rounded-full bg-primary"></span>
                {{ t('cards.viewsLabel', { count: day.views }) }}
              </div>
              <div class="flex items-center gap-2">
                <span class="w-2 h-2 rounded-full bg-green-500"></span>
                {{ t('cards.vcardLabel', { count: day.vcard_downloads }) }}
              </div>
            </div>
            
            <div 
              class="w-full bg-green-500 rounded-t-sm transition-all duration-500 hover:opacity-80" 
              :style="{ height: `${(day.vcard_downloads / maxDailyValue) * 100}%` }"
            ></div>
            
            <div 
              class="w-full bg-primary rounded-t-sm transition-all duration-500 hover:opacity-80 -mt-px" 
              :style="{ height: `${(day.views / maxDailyValue) * 100}%` }"
            ></div>
          </div>
        </div>

        <p class="text-center text-xs text-gray-400 mt-4">
          {{ t('cards.chartHint') }}
        </p>
      </div>
    </div>
  </div>
</template>

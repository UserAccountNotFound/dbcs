<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { adminApi } from '../../api/admin';
import type { ExtendedAnalytics, AnalyticsPeriod } from '../../types/analytics';
import PeriodSelector from '../../components/analytics/PeriodSelector.vue';
import LineChart from '../../components/analytics/LineChart.vue';
import BarChart from '../../components/analytics/BarChart.vue';
import DonutChart from '../../components/analytics/DonutChart.vue';
import HeatmapChart from '../../components/analytics/HeatmapChart.vue';

const period = ref<AnalyticsPeriod>('30d');
const data = ref<ExtendedAnalytics | null>(null);
const isLoading = ref(true);
const error = ref('');

async function load() {
  isLoading.value = true;
  error.value = '';
  try {
    data.value = await adminApi.getExtendedAnalytics(period.value);
  } catch (e: any) {
    error.value = e.response?.data?.detail || 'Не удалось загрузить аналитику';
  } finally {
    isLoading.value = false;
  }
}

onMounted(load);
watch(period, load);

const totals = computed(() => {
  if (!data.value) return { views: 0, downloads: 0 };
  return {
    views: data.value.time_series.reduce((sum, d) => sum + d.views, 0),
    downloads: data.value.time_series.reduce((sum, d) => sum + d.downloads, 0),
  };
});

const referrersBarData = computed(() => {
  if (!data.value) return [];
  const colors = ['#0f766e', '#0d9488', '#14b8a6', '#2dd4bf', '#5eead4', '#99f6e4', '#ccfbf1', '#f0fdfa', '#a7f3d0', '#6ee7b7'];
  return data.value.referrers.map((r, i) => ({
    label: r.source,
    value: r.count,
    color: colors[i % colors.length],
  }));
});

const devicesDonutData = computed(() => {
  if (!data.value) return [];
  const colorMap: Record<string, string> = {
    Desktop: '#0f766e',
    Mobile: '#14b8a6',
    Tablet: '#5eead4',
    Unknown: '#d1d5db',
  };
  return data.value.devices.map(d => ({
    label: d.device,
    value: d.count,
    color: colorMap[d.device] || '#d1d5db',
  }));
});

function formatNumber(n: number): string {
  return n.toLocaleString('ru-RU');
}
</script>

<template>
  <div>
    <div class="flex flex-wrap justify-between items-center gap-4 mb-6">
      <div>
        <h2 class="text-2xl font-bold text-gray-900">Расширенная аналитика</h2>
        <p class="text-sm text-gray-500 mt-1">
          Детальная статистика системы
          <span v-if="data"> • Обновлено: {{ new Date(data.generated_at).toLocaleString('ru-RU') }}</span>
        </p>
      </div>
      <PeriodSelector v-model="period" />
    </div>

    <div v-if="isLoading" class="flex justify-center py-20">
      <div class="animate-spin rounded-full h-10 w-10 border-b-2 border-primary"></div>
    </div>

    <div v-else-if="error" class="text-center py-12 bg-red-50 rounded-xl">
      <p class="text-red-600">{{ error }}</p>
      <button @click="load" class="mt-4 btn-primary">Попробовать снова</button>
    </div>

    <div v-else-if="data" class="space-y-6">
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div class="bg-white rounded-xl border border-gray-100 p-5 shadow-sm">
          <div class="text-sm text-gray-500">Всего просмотров</div>
          <div class="text-3xl font-bold text-gray-900 mt-1">{{ formatNumber(totals.views) }}</div>
        </div>
        <div class="bg-white rounded-xl border border-gray-100 p-5 shadow-sm">
          <div class="text-sm text-gray-500">Скачиваний vCard</div>
          <div class="text-3xl font-bold text-gray-900 mt-1">{{ formatNumber(totals.downloads) }}</div>
        </div>
        <div class="bg-white rounded-xl border border-gray-100 p-5 shadow-sm">
          <div class="text-sm text-gray-500">Конверсия</div>
          <div class="text-3xl font-bold text-gray-900 mt-1">
            {{ totals.views > 0 ? ((totals.downloads / totals.views) * 100).toFixed(1) : '0' }}%
          </div>
        </div>
        <div class="bg-white rounded-xl border border-gray-100 p-5 shadow-sm">
          <div class="text-sm text-gray-500">Период</div>
          <div class="text-3xl font-bold text-gray-900 mt-1">
            {{ data.time_series.length }} дн.
          </div>
        </div>
      </div>

      <div class="bg-white rounded-xl border border-gray-100 p-6 shadow-sm">
        <h3 class="text-lg font-semibold text-gray-900 mb-4">Тренды просмотров и скачиваний</h3>
        <LineChart :data="data.time_series" />
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div class="bg-white rounded-xl border border-gray-100 p-6 shadow-sm lg:col-span-2">
          <h3 class="text-lg font-semibold text-gray-900 mb-4">Активность по дням недели и часам</h3>
          <HeatmapChart :data="data.hourly_heatmap" />
        </div>

        <div class="bg-white rounded-xl border border-gray-100 p-6 shadow-sm">
          <h3 class="text-lg font-semibold text-gray-900 mb-4">Устройства</h3>
          <DonutChart :data="devicesDonutData" />
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div class="bg-white rounded-xl border border-gray-100 p-6 shadow-sm">
          <h3 class="text-lg font-semibold text-gray-900 mb-4">Источники трафика</h3>
          <BarChart v-if="data.referrers.length > 0" :data="referrersBarData" />
          <p v-else class="text-gray-500 text-sm py-8 text-center">Нет данных об источниках</p>
        </div>

        <div class="bg-white rounded-xl border border-gray-100 p-6 shadow-sm">
          <h3 class="text-lg font-semibold text-gray-900 mb-4">Топ-10 визиток</h3>
          <div v-if="data.top_cards.length === 0" class="text-gray-500 text-sm py-8 text-center">
            Нет данных
          </div>
          <div v-else class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="text-left text-xs text-gray-500 uppercase border-b">
                  <th class="pb-2 pr-2">#</th>
                  <th class="pb-2">Визитка</th>
                  <th class="pb-2 text-right">👁️</th>
                  <th class="pb-2 text-right">📥</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(card, i) in data.top_cards" :key="card.id" class="border-b border-gray-50 last:border-0">
                  <td class="py-2 pr-2 text-gray-400">{{ i + 1 }}</td>
                  <td class="py-2">
                    <div class="font-medium text-gray-900">{{ card.title }}</div>
                    <div class="text-xs text-gray-500">{{ card.full_name }} • {{ card.user_email }}</div>
                  </td>
                  <td class="py-2 text-right font-semibold text-gray-900">{{ formatNumber(card.views) }}</td>
                  <td class="py-2 text-right text-gray-600">{{ formatNumber(card.downloads) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-xl border border-gray-100 p-6 shadow-sm">
        <h3 class="text-lg font-semibold text-gray-900 mb-4">Топ-10 активных пользователей</h3>
        <div v-if="data.top_users.length === 0" class="text-gray-500 text-sm py-8 text-center">
          Нет данных
        </div>
        <div v-else class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="text-left text-xs text-gray-500 uppercase border-b">
                <th class="pb-2 pr-2">#</th>
                <th class="pb-2">Пользователь</th>
                <th class="pb-2 text-right">Визиток</th>
                <th class="pb-2 text-right">Просмотров</th>
                <th class="pb-2 text-right">Скачиваний</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(user, i) in data.top_users" :key="user.id" class="border-b border-gray-50 last:border-0">
                <td class="py-2 pr-2 text-gray-400">{{ i + 1 }}</td>
                <td class="py-2">
                  <div class="font-medium text-gray-900">{{ user.full_name }}</div>
                  <div class="text-xs text-gray-500">{{ user.email }}</div>
                </td>
                <td class="py-2 text-right text-gray-600">{{ user.cards_count }}</td>
                <td class="py-2 text-right font-semibold text-gray-900">{{ formatNumber(user.views) }}</td>
                <td class="py-2 text-right text-gray-600">{{ formatNumber(user.downloads) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

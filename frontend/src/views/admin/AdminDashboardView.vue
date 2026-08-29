<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { adminApi } from '../../api/admin';
import type { OverviewStats } from '../../types/admin';
import type { ExtendedAnalytics, AnalyticsPeriod } from '../../types/analytics';
import PeriodSelector from '../../components/analytics/PeriodSelector.vue';
import LineChart from '../../components/analytics/LineChart.vue';
import BarChart from '../../components/analytics/BarChart.vue';
import DonutChart from '../../components/analytics/DonutChart.vue';
import HeatmapChart from '../../components/analytics/HeatmapChart.vue';
import { getAxiosErrorMessage } from '../../utils/apiError';
import { deviceHint, referrerHint } from '../../utils/analyticsHints';
import { useLocaleDate } from '../../composables/useLocaleDate';

const { t } = useI18n();
const { bcp47, formatDateTime } = useLocaleDate();
const overview = ref<OverviewStats | null>(null);
const data = ref<ExtendedAnalytics | null>(null);
const period = ref<AnalyticsPeriod>('30d');
const isLoadingOverview = ref(true);
const isLoadingAnalytics = ref(true);
const error = ref('');

const overviewCards = computed(() => [
  { key: 'total_users', label: t('admin.stats.totalUsers'), color: 'bg-blue-500' },
  { key: 'active_users', label: t('admin.stats.activeUsers'), color: 'bg-green-500' },
  { key: 'total_cards', label: t('admin.stats.totalCards'), color: 'bg-purple-500' },
  { key: 'active_cards', label: t('admin.stats.activeCards'), color: 'bg-teal-500' },
  { key: 'total_visits', label: t('admin.stats.totalVisits'), color: 'bg-orange-500' },
  { key: 'total_vcard_downloads', label: t('admin.stats.totalVcardDownloads'), color: 'bg-pink-500' },
] as const);

async function loadOverview() {
  isLoadingOverview.value = true;
  try {
    overview.value = await adminApi.getOverviewStats();
  } catch (e) {
    console.error('Failed to load overview stats', e);
  } finally {
    isLoadingOverview.value = false;
  }
}

async function loadAnalytics() {
  isLoadingAnalytics.value = true;
  error.value = '';
  try {
    data.value = await adminApi.getExtendedAnalytics(period.value);
  } catch (e: unknown) {
    error.value = getAxiosErrorMessage(e, t('errors.analyticsLoad'));
  } finally {
    isLoadingAnalytics.value = false;
  }
}

onMounted(() => {
  void loadOverview();
  void loadAnalytics();
});
watch(period, () => {
  void loadAnalytics();
});

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
    hint: referrerHint(r.source),
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
  return data.value.devices.map((d) => ({
    label: d.device,
    value: d.count,
    color: colorMap[d.device] || '#d1d5db',
    hint: deviceHint(d.device),
  }));
});

function formatNumber(n: number): string {
  return n.toLocaleString(bcp47.value);
}
</script>

<template>
  <div class="space-y-8">
    <div class="flex flex-wrap justify-between items-start gap-4">
      <div>
        <h2 class="text-2xl font-bold text-gray-900">{{ t('admin.overviewTitle') }}</h2>
        <p class="text-sm text-gray-500 mt-1">
          {{ t('admin.overviewSubtitle') }}
          <span v-if="data">{{ t('admin.updatedAt', { date: formatDateTime(data.generated_at) }) }}</span>
        </p>
      </div>
      <PeriodSelector v-model="period" />
    </div>

    <!-- Сводка по системе -->
    <section>
      <h3 class="text-lg font-semibold text-gray-900 mb-4">{{ t('admin.systemSummary') }}</h3>

      <div v-if="isLoadingOverview" class="flex justify-center py-12">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>

      <div v-else-if="overview" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div
          v-for="card in overviewCards"
          :key="card.key"
          class="bg-white rounded-xl shadow-sm p-6 border border-gray-100"
        >
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-gray-500">{{ card.label }}</p>
              <p class="text-3xl font-bold mt-2 text-gray-900">
                {{ formatNumber(overview[card.key]) }}
              </p>
            </div>
            <div :class="card.color" class="w-12 h-12 rounded-lg opacity-20"></div>
          </div>
        </div>
      </div>
    </section>

    <!-- Аналитика за период -->
    <section>
      <h3 class="text-lg font-semibold text-gray-900 mb-4">{{ t('admin.periodAnalytics') }}</h3>

      <div v-if="isLoadingAnalytics" class="flex justify-center py-20">
        <div class="animate-spin rounded-full h-10 w-10 border-b-2 border-primary"></div>
      </div>

      <div v-else-if="error" class="text-center py-12 bg-red-50 rounded-xl">
        <p class="text-red-600">{{ error }}</p>
        <button @click="loadAnalytics" class="mt-4 btn-primary">{{ t('common.retry') }}</button>
      </div>

      <div v-else-if="data" class="space-y-6">
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div class="bg-white rounded-xl border border-gray-100 p-5 shadow-sm">
            <div class="text-sm text-gray-500">{{ t('admin.viewsPeriod') }}</div>
            <div class="text-3xl font-bold text-gray-900 mt-1">{{ formatNumber(totals.views) }}</div>
          </div>
          <div class="bg-white rounded-xl border border-gray-100 p-5 shadow-sm">
            <div class="text-sm text-gray-500">{{ t('admin.downloadsPeriod') }}</div>
            <div class="text-3xl font-bold text-gray-900 mt-1">{{ formatNumber(totals.downloads) }}</div>
          </div>
          <div class="bg-white rounded-xl border border-gray-100 p-5 shadow-sm">
            <div class="text-sm text-gray-500">{{ t('admin.conversion') }}</div>
            <div class="text-3xl font-bold text-gray-900 mt-1">
              {{ totals.views > 0 ? ((totals.downloads / totals.views) * 100).toFixed(1) : '0' }}%
            </div>
          </div>
          <div class="bg-white rounded-xl border border-gray-100 p-5 shadow-sm">
            <div class="text-sm text-gray-500">{{ t('admin.period') }}</div>
            <div class="text-3xl font-bold text-gray-900 mt-1">
              {{ t('admin.days', { count: data.time_series.length }) }}
            </div>
          </div>
        </div>

        <div class="bg-white rounded-xl border border-gray-100 p-6 shadow-sm">
          <h4 class="text-lg font-semibold text-gray-900 mb-4">{{ t('admin.trends') }}</h4>
          <LineChart :data="data.time_series" />
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div class="bg-white rounded-xl border border-gray-100 p-6 shadow-sm lg:col-span-2">
            <h4 class="text-lg font-semibold text-gray-900 mb-4">{{ t('admin.heatmap') }}</h4>
            <HeatmapChart :data="data.hourly_heatmap" />
          </div>

          <div class="bg-white rounded-xl border border-gray-100 p-6 shadow-sm">
            <h4 class="text-lg font-semibold text-gray-900 mb-4">{{ t('admin.devices') }}</h4>
            <DonutChart :data="devicesDonutData" />
          </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div class="bg-white rounded-xl border border-gray-100 p-6 shadow-sm">
            <h4 class="text-lg font-semibold text-gray-900 mb-1">{{ t('admin.referrers') }}</h4>
            <p class="text-xs text-gray-500 mb-4">{{ t('admin.referrersHint') }}</p>
            <BarChart v-if="data.referrers.length > 0" :data="referrersBarData" />
            <p v-else class="text-gray-500 text-sm py-8 text-center">{{ t('admin.noReferrers') }}</p>
          </div>

          <div class="bg-white rounded-xl border border-gray-100 p-6 shadow-sm">
            <h4 class="text-lg font-semibold text-gray-900 mb-4">{{ t('admin.topCards') }}</h4>
            <div v-if="data.top_cards.length === 0" class="text-gray-500 text-sm py-8 text-center">
              {{ t('common.noData') }}
            </div>
            <div v-else class="overflow-x-auto">
              <table class="w-full text-sm">
                <thead>
                  <tr class="text-left text-xs text-gray-500 uppercase border-b">
                    <th class="pb-2 pr-2">#</th>
                    <th class="pb-2">{{ t('cards.columnCard') }}</th>
                    <th class="pb-2 text-right">👁️</th>
                    <th class="pb-2 text-right">📥</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="(card, i) in data.top_cards"
                    :key="card.id"
                    class="border-b border-gray-50 last:border-0"
                  >
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
          <h4 class="text-lg font-semibold text-gray-900 mb-4">{{ t('admin.topUsers') }}</h4>
          <div v-if="data.top_users.length === 0" class="text-gray-500 text-sm py-8 text-center">
            {{ t('common.noData') }}
          </div>
          <div v-else class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="text-left text-xs text-gray-500 uppercase border-b">
                  <th class="pb-2 pr-2">#</th>
                  <th class="pb-2">{{ t('admin.columnUser') }}</th>
                  <th class="pb-2 text-right">{{ t('admin.columnCards') }}</th>
                  <th class="pb-2 text-right">{{ t('admin.columnViewsRight') }}</th>
                  <th class="pb-2 text-right">{{ t('admin.columnDownloadsRight') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="(user, i) in data.top_users"
                  :key="user.id"
                  class="border-b border-gray-50 last:border-0"
                >
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
    </section>
  </div>
</template>

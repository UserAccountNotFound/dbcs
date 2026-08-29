<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { useLocaleDate } from '../../composables/useLocaleDate';

const props = defineProps<{
  data: { date: string; views: number; downloads: number }[];
  height?: number;
}>();

const { t } = useI18n();
const { bcp47 } = useLocaleDate();

const HEIGHT = computed(() => props.height || 240);
const WIDTH = 600;
const PADDING = { top: 20, right: 20, bottom: 40, left: 50 };

const chartWidth = computed(() => WIDTH - PADDING.left - PADDING.right);
const chartHeight = computed(() => HEIGHT.value - PADDING.top - PADDING.bottom);

const maxValue = computed(() => {
  if (props.data.length === 0) return 10;
  const max = Math.max(...props.data.flatMap(d => [d.views, d.downloads]));
  return max > 0 ? max * 1.1 : 10;
});

const xStep = computed(() => {
  if (props.data.length <= 1) return chartWidth.value;
  return chartWidth.value / (props.data.length - 1);
});

const toX = (i: number) => PADDING.left + i * xStep.value;
const toY = (val: number) => PADDING.top + chartHeight.value - (val / maxValue.value) * chartHeight.value;

const viewsPath = computed(() => {
  if (props.data.length === 0) return '';
  return props.data
    .map((d, i) => `${i === 0 ? 'M' : 'L'} ${toX(i)} ${toY(d.views)}`)
    .join(' ');
});

const downloadsPath = computed(() => {
  if (props.data.length === 0) return '';
  return props.data
    .map((d, i) => `${i === 0 ? 'M' : 'L'} ${toX(i)} ${toY(d.downloads)}`)
    .join(' ');
});

const viewsAreaPath = computed(() => {
  if (props.data.length === 0) return '';
  const bottomY = PADDING.top + chartHeight.value;
  const line = props.data.map((d, i) => `${i === 0 ? 'M' : 'L'} ${toX(i)} ${toY(d.views)}`).join(' ');
  return `${line} L ${toX(props.data.length - 1)} ${bottomY} L ${toX(0)} ${bottomY} Z`;
});

const gridLines = computed(() => {
  const lines = [];
  const steps = 5;
  for (let i = 0; i <= steps; i++) {
    const y = PADDING.top + (chartHeight.value / steps) * i;
    const value = Math.round((maxValue.value / steps) * (steps - i));
    lines.push({ y, value });
  }
  return lines;
});

const dateLabels = computed(() => {
  if (props.data.length === 0) return [];
  const labelCount = Math.min(7, props.data.length);
  const step = Math.max(1, Math.floor(props.data.length / labelCount));
  const labels = [];
  for (let i = 0; i < props.data.length; i += step) {
    const d = new Date(props.data[i].date);
    labels.push({
      x: toX(i),
      label: d.toLocaleDateString(bcp47.value, { day: 'numeric', month: 'short' }),
    });
  }
  return labels;
});
</script>

<template>
  <div class="w-full">
    <svg :viewBox="`0 0 ${WIDTH} ${HEIGHT}`" class="w-full h-auto" preserveAspectRatio="xMidYMid meet">
      <g>
        <line
          v-for="(line, i) in gridLines"
          :key="i"
          :x1="PADDING.left"
          :x2="WIDTH - PADDING.right"
          :y1="line.y"
          :y2="line.y"
          stroke="#e5e7eb"
          stroke-width="1"
          stroke-dasharray="2 4"
        />
        <text
          v-for="(line, i) in gridLines"
          :key="'lbl-' + i"
          :x="PADDING.left - 8"
          :y="line.y + 4"
          text-anchor="end"
          class="text-xs fill-gray-400"
        >
          {{ line.value }}
        </text>
      </g>

      <g>
        <text
          v-for="(lbl, i) in dateLabels"
          :key="i"
          :x="lbl.x"
          :y="HEIGHT - PADDING.bottom + 20"
          text-anchor="middle"
          class="text-xs fill-gray-500"
        >
          {{ lbl.label }}
        </text>
      </g>

      <path :d="viewsAreaPath" fill="#0f766e" fill-opacity="0.1" />
      <path :d="downloadsPath" fill="none" stroke="#10b981" stroke-width="2" stroke-linejoin="round" />
      <path :d="viewsPath" fill="none" stroke="#0f766e" stroke-width="2.5" stroke-linejoin="round" />

      <template v-if="data.length <= 30">
        <circle
          v-for="(d, i) in data"
          :key="'pv-' + i"
          :cx="toX(i)"
          :cy="toY(d.views)"
          r="3"
          fill="#0f766e"
        />
        <circle
          v-for="(d, i) in data"
          :key="'pd-' + i"
          :cx="toX(i)"
          :cy="toY(d.downloads)"
          r="3"
          fill="#10b981"
        />
      </template>
    </svg>

    <div class="flex justify-center gap-6 mt-3 text-sm">
      <div class="flex items-center gap-2">
        <div class="w-3 h-3 rounded-sm" style="background: #0f766e"></div>
        <span class="text-gray-600">{{ t('analytics.chartViews') }}</span>
      </div>
      <div class="flex items-center gap-2">
        <div class="w-3 h-3 rounded-sm" style="background: #10b981"></div>
        <span class="text-gray-600">{{ t('analytics.chartVcardDownloads') }}</span>
      </div>
    </div>
  </div>
</template>

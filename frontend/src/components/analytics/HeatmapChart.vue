<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { useLocaleDate } from '../../composables/useLocaleDate';

const props = defineProps<{
  data: { day_of_week: number; hour: number; count: number }[];
}>();

const { t } = useI18n();
const { bcp47 } = useLocaleDate();

const HOURS = 24;
const CELL_SIZE = 22;
const GAP = 2;
const LEFT_PAD = 30;
const TOP_PAD = 24;

// 2024-01-01 is Monday (day_of_week 0 = Mon … 6 = Sun)
const WEEKDAY_BASE = new Date(2024, 0, 1);

function weekdayShort(dayIndex: number): string {
  const date = new Date(WEEKDAY_BASE);
  date.setDate(WEEKDAY_BASE.getDate() + dayIndex);
  return date.toLocaleDateString(bcp47.value, { weekday: 'short' });
}

const dayLabels = computed(() =>
  Array.from({ length: 7 }, (_, i) => weekdayShort(i)),
);

const WIDTH = computed(() => LEFT_PAD + HOURS * (CELL_SIZE + GAP));
const HEIGHT = computed(() => TOP_PAD + 7 * (CELL_SIZE + GAP));

const maxValue = computed(() => {
  if (props.data.length === 0) return 1;
  return Math.max(...props.data.map(d => d.count), 1);
});

const cells = computed(() => {
  const matrix: { day: number; hour: number; count: number; color: string }[] = [];
  const dataMap = new Map(props.data.map(d => [`${d.day_of_week}-${d.hour}`, d.count]));

  for (let day = 0; day < 7; day++) {
    for (let hour = 0; hour < HOURS; hour++) {
      const count = dataMap.get(`${day}-${hour}`) || 0;
      const intensity = maxValue.value > 0 ? count / maxValue.value : 0;
      matrix.push({ day, hour, count, color: getColor(intensity) });
    }
  }
  return matrix;
});

function getColor(intensity: number): string {
  const palette = ['#f0fdfa', '#ccfbf1', '#5eead4', '#14b8a6', '#0d9488', '#0f766e'];
  const idx = Math.min(palette.length - 1, Math.floor(intensity * palette.length));
  return palette[idx];
}

function cellTooltip(day: number, hour: number, count: number): string {
  return t('analytics.heatmapTooltip', {
    day: dayLabels.value[day],
    hour,
    count,
  });
}

const hoursLabels = computed(() =>
  [0, 4, 8, 12, 16, 20].map(h => ({
    hour: h,
    x: LEFT_PAD + h * (CELL_SIZE + GAP) + CELL_SIZE / 2,
  })),
);
</script>

<template>
  <div class="w-full overflow-x-auto">
    <svg :viewBox="`0 0 ${WIDTH} ${HEIGHT}`" class="w-full h-auto" preserveAspectRatio="xMidYMid meet">
      <text
        v-for="h in hoursLabels"
        :key="'h-' + h.hour"
        :x="h.x"
        :y="TOP_PAD - 8"
        text-anchor="middle"
        class="text-[10px] fill-gray-500"
      >
        {{ h.hour }}:00
      </text>

      <template v-for="day in 7" :key="'day-' + day">
        <text
          :x="LEFT_PAD - 8"
          :y="TOP_PAD + (day - 1) * (CELL_SIZE + GAP) + CELL_SIZE / 2 + 4"
          text-anchor="end"
          class="text-[11px] fill-gray-600 font-medium"
        >
          {{ dayLabels[day - 1] }}
        </text>

        <g v-for="hour in 24" :key="'c-' + day + '-' + hour">
          <rect
            :x="LEFT_PAD + (hour - 1) * (CELL_SIZE + GAP)"
            :y="TOP_PAD + (day - 1) * (CELL_SIZE + GAP)"
            :width="CELL_SIZE"
            :height="CELL_SIZE"
            :fill="cells[(day - 1) * 24 + (hour - 1)].color"
            rx="3"
          >
            <title>
              {{ cellTooltip(day - 1, hour - 1, cells[(day - 1) * 24 + (hour - 1)].count) }}
            </title>
          </rect>
        </g>
      </template>
    </svg>

    <div class="flex items-center justify-end gap-2 mt-3 text-xs text-gray-500">
      <span>{{ t('analytics.heatmapLess') }}</span>
      <div class="flex gap-0.5">
        <div class="w-4 h-4 rounded-sm" style="background: #f0fdfa"></div>
        <div class="w-4 h-4 rounded-sm" style="background: #ccfbf1"></div>
        <div class="w-4 h-4 rounded-sm" style="background: #5eead4"></div>
        <div class="w-4 h-4 rounded-sm" style="background: #14b8a6"></div>
        <div class="w-4 h-4 rounded-sm" style="background: #0d9488"></div>
        <div class="w-4 h-4 rounded-sm" style="background: #0f766e"></div>
      </div>
      <span>{{ t('analytics.heatmapMore') }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps<{
  data: { label: string; value: number; color?: string }[];
  height?: number;
}>();

const HEIGHT = computed(() => props.height || 280);
const WIDTH = 600;
const PADDING = { top: 20, right: 20, bottom: 20, left: 140 };

const maxValue = computed(() => {
  if (props.data.length === 0) return 10;
  return Math.max(...props.data.map(d => d.value)) * 1.1;
});

const barHeight = computed(() => {
  if (props.data.length === 0) return 20;
  const available = HEIGHT.value - PADDING.top - PADDING.bottom;
  return Math.min(28, available / props.data.length - 6);
});

const barGap = 6;

const toX = (val: number) => PADDING.left + (val / maxValue.value) * (WIDTH - PADDING.left - PADDING.right);
</script>

<template>
  <svg :viewBox="`0 0 ${WIDTH} ${HEIGHT}`" class="w-full h-auto" preserveAspectRatio="xMidYMid meet">
    <g>
      <template v-for="(d, i) in data" :key="i">
        <!-- Подпись слева -->
        <text
          :x="PADDING.left - 10"
          :y="PADDING.top + i * (barHeight + barGap) + barHeight / 2 + 4"
          text-anchor="end"
          class="text-xs fill-gray-700 font-medium"
        >
          {{ d.label.length > 18 ? d.label.slice(0, 16) + '…' : d.label }}
        </text>

        <!-- Серая подложка -->
        <rect
          :x="PADDING.left"
          :y="PADDING.top + i * (barHeight + barGap)"
          :width="WIDTH - PADDING.left - PADDING.right"
          :height="barHeight"
          fill="#f3f4f6"
          rx="4"
        />

        <!-- Цветной бар -->
        <rect
          :x="PADDING.left"
          :y="PADDING.top + i * (barHeight + barGap)"
          :width="toX(d.value) - PADDING.left"
          :height="barHeight"
          :fill="d.color || '#0f766e'"
          rx="4"
        />

        <!-- Значение справа -->
        <text
          :x="toX(d.value) + 6"
          :y="PADDING.top + i * (barHeight + barGap) + barHeight / 2 + 4"
          class="text-xs fill-gray-600 font-semibold"
        >
          {{ d.value }}
        </text>
      </template>
    </g>
  </svg>
</template>
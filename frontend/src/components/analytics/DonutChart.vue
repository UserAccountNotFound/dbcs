<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps<{
  data: { label: string; value: number; color: string }[];
  size?: number;
}>();

const SIZE = computed(() => props.size || 220);
const CENTER = computed(() => SIZE.value / 2);
const RADIUS = computed(() => SIZE.value / 2 - 10);
const INNER_RADIUS = computed(() => RADIUS.value * 0.6);

const total = computed(() => props.data.reduce((sum, d) => sum + d.value, 0));

interface Segment {
  label: string;
  value: number;
  percent: number;
  color: string;
  path: string;
}

const segments = computed<Segment[]>(() => {
  if (total.value === 0) return [];
  
  let currentAngle = -Math.PI / 2; // Старт сверху
  const segs: Segment[] = [];
  
  for (const d of props.data) {
    const percent = d.value / total.value;
    const angle = percent * 2 * Math.PI;
    const startAngle = currentAngle;
    const endAngle = currentAngle + angle;
    
    const x1 = CENTER.value + RADIUS.value * Math.cos(startAngle);
    const y1 = CENTER.value + RADIUS.value * Math.sin(startAngle);
    const x2 = CENTER.value + RADIUS.value * Math.cos(endAngle);
    const y2 = CENTER.value + RADIUS.value * Math.sin(endAngle);
    const x3 = CENTER.value + INNER_RADIUS.value * Math.cos(endAngle);
    const y3 = CENTER.value + INNER_RADIUS.value * Math.sin(endAngle);
    const x4 = CENTER.value + INNER_RADIUS.value * Math.cos(startAngle);
    const y4 = CENTER.value + INNER_RADIUS.value * Math.sin(startAngle);
    
    const largeArc = angle > Math.PI ? 1 : 0;
    
    const path = [
      `M ${x1} ${y1}`,
      `A ${RADIUS.value} ${RADIUS.value} 0 ${largeArc} 1 ${x2} ${y2}`,
      `L ${x3} ${y3}`,
      `A ${INNER_RADIUS.value} ${INNER_RADIUS.value} 0 ${largeArc} 0 ${x4} ${y4}`,
      'Z',
    ].join(' ');
    
    segs.push({
      label: d.label,
      value: d.value,
      percent,
      color: d.color,
      path,
    });
    
    currentAngle = endAngle;
  }
  
  return segs;
});
</script>

<template>
  <div class="flex items-center gap-6">
    <svg :viewBox="`0 0 ${SIZE} ${SIZE}`" :width="SIZE" :height="SIZE" class="flex-shrink-0">
      <path
        v-for="(seg, i) in segments"
        :key="i"
        :d="seg.path"
        :fill="seg.color"
        stroke="white"
        stroke-width="2"
      />
      <!-- Текст в центре -->
      <text
        :x="CENTER"
        :y="CENTER - 8"
        text-anchor="middle"
        class="text-2xl fill-gray-900 font-bold"
      >
        {{ total }}
      </text>
      <text
        :x="CENTER"
        :y="CENTER + 14"
        text-anchor="middle"
        class="text-xs fill-gray-500"
      >
        всего
      </text>
    </svg>

    <!-- Легенда -->
    <div class="flex-1 space-y-2">
      <div
        v-for="seg in segments"
        :key="seg.label"
        class="flex items-center justify-between text-sm"
      >
        <div class="flex items-center gap-2">
          <div class="w-3 h-3 rounded-sm" :style="{ background: seg.color }"></div>
          <span class="text-gray-700">{{ seg.label }}</span>
        </div>
        <div class="text-right">
          <span class="font-semibold text-gray-900">{{ seg.value }}</span>
          <span class="text-gray-400 ml-1">({{ (seg.percent * 100).toFixed(1) }}%)</span>
        </div>
      </div>
    </div>
  </div>
</template>
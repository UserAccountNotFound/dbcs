<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue';

const props = defineProps<{
  data: { label: string; value: number; color: string; hint?: string }[];
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
  hint?: string;
}

const segments = computed<Segment[]>(() => {
  if (total.value === 0) return [];

  let currentAngle = -Math.PI / 2;
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
      hint: d.hint,
    });

    currentAngle = endAngle;
  }

  return segs;
});

const wrapRef = ref<HTMLElement | null>(null);
const tip = ref<{ text: string; x: number; y: number } | null>(null);
let hideTimer: number | undefined;

function showTip(event: MouseEvent | TouchEvent, text: string | undefined) {
  if (!text || !wrapRef.value) return;
  if (hideTimer) {
    window.clearTimeout(hideTimer);
    hideTimer = undefined;
  }
  const rect = wrapRef.value.getBoundingClientRect();
  let clientX = 0;
  let clientY = 0;
  if ('touches' in event && event.touches[0]) {
    clientX = event.touches[0].clientX;
    clientY = event.touches[0].clientY;
  } else if ('clientX' in event) {
    clientX = event.clientX;
    clientY = event.clientY;
  }
  tip.value = {
    text,
    x: Math.min(Math.max(12, clientX - rect.left + 8), rect.width - 12),
    y: Math.max(12, clientY - rect.top - 8),
  };
}

function scheduleHide() {
  if (hideTimer) window.clearTimeout(hideTimer);
  hideTimer = window.setTimeout(() => {
    tip.value = null;
  }, 120);
}

function hideTip() {
  if (hideTimer) window.clearTimeout(hideTimer);
  tip.value = null;
}

function onDocPointerDown(e: Event) {
  if (!wrapRef.value) return;
  if (!wrapRef.value.contains(e.target as Node)) hideTip();
}

onMounted(() => {
  document.addEventListener('pointerdown', onDocPointerDown);
});

onBeforeUnmount(() => {
  document.removeEventListener('pointerdown', onDocPointerDown);
  if (hideTimer) window.clearTimeout(hideTimer);
});
</script>

<template>
  <div ref="wrapRef" class="relative flex items-center gap-6">
    <svg :viewBox="`0 0 ${SIZE} ${SIZE}`" :width="SIZE" :height="SIZE" class="flex-shrink-0">
      <path
        v-for="(seg, i) in segments"
        :key="i"
        :d="seg.path"
        :fill="seg.color"
        stroke="white"
        stroke-width="2"
        class="cursor-help"
        @mouseenter="(e) => showTip(e, seg.hint)"
        @mousemove="(e) => showTip(e, seg.hint)"
        @mouseleave="scheduleHide"
        @click.stop="(e) => showTip(e, seg.hint)"
        @touchstart.passive="(e) => showTip(e, seg.hint)"
      >
        <title v-if="seg.hint">{{ seg.hint }}</title>
      </path>
      <text
        :x="CENTER"
        :y="CENTER - 8"
        text-anchor="middle"
        class="text-2xl fill-gray-900 font-bold pointer-events-none"
      >
        {{ total }}
      </text>
      <text
        :x="CENTER"
        :y="CENTER + 14"
        text-anchor="middle"
        class="text-xs fill-gray-500 pointer-events-none"
      >
        всего
      </text>
    </svg>

    <div class="flex-1 space-y-2">
      <div
        v-for="seg in segments"
        :key="seg.label"
        class="flex items-center justify-between text-sm cursor-help rounded-md px-1 -mx-1 hover:bg-gray-50"
        :title="seg.hint"
        @mouseenter="(e) => showTip(e, seg.hint)"
        @mousemove="(e) => showTip(e, seg.hint)"
        @mouseleave="scheduleHide"
        @click.stop="(e) => showTip(e, seg.hint)"
        @touchstart.passive="(e) => showTip(e, seg.hint)"
      >
        <div class="flex items-center gap-2">
          <div class="w-3 h-3 rounded-sm" :style="{ background: seg.color }"></div>
          <span class="text-gray-700 underline decoration-dotted decoration-gray-300 underline-offset-2">
            {{ seg.label }}
          </span>
        </div>
        <div class="text-right">
          <span class="font-semibold text-gray-900">{{ seg.value }}</span>
          <span class="text-gray-400 ml-1">({{ (seg.percent * 100).toFixed(1) }}%)</span>
        </div>
      </div>
    </div>

    <div
      v-if="tip"
      class="pointer-events-none absolute z-20 max-w-[240px] rounded-lg bg-gray-900 px-3 py-2 text-xs leading-snug text-white shadow-lg"
      :style="{ left: `${tip.x}px`, top: `${tip.y}px`, transform: 'translate(-20%, -110%)' }"
    >
      {{ tip.text }}
    </div>
  </div>
</template>

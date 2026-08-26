<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue';

const props = defineProps<{
  data: { label: string; value: number; color?: string; hint?: string }[];
  height?: number;
}>();

const HEIGHT = computed(() => props.height || 280);
const WIDTH = 600;
const PADDING = { top: 20, right: 20, bottom: 20, left: 140 };

const maxValue = computed(() => {
  if (props.data.length === 0) return 10;
  return Math.max(...props.data.map((d) => d.value)) * 1.1;
});

const barHeight = computed(() => {
  if (props.data.length === 0) return 20;
  const available = HEIGHT.value - PADDING.top - PADDING.bottom;
  return Math.min(28, available / props.data.length - 6);
});

const barGap = 6;

const toX = (val: number) =>
  PADDING.left + (val / maxValue.value) * (WIDTH - PADDING.left - PADDING.right);

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
    x: Math.min(Math.max(12, clientX - rect.left + 12), rect.width - 12),
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
  if (!wrapRef.value.contains(e.target as Node)) {
    hideTip();
  }
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
  <div ref="wrapRef" class="relative w-full select-none">
    <svg :viewBox="`0 0 ${WIDTH} ${HEIGHT}`" class="w-full h-auto" preserveAspectRatio="xMidYMid meet">
      <g>
        <template v-for="(d, i) in data" :key="i">
          <!-- Невидимая зона для hover/tap по всей строке -->
          <rect
            :x="0"
            :y="PADDING.top + i * (barHeight + barGap) - 2"
            :width="WIDTH"
            :height="barHeight + 4"
            fill="transparent"
            class="cursor-help"
            @mouseenter="(e) => showTip(e, d.hint)"
            @mousemove="(e) => showTip(e, d.hint)"
            @mouseleave="scheduleHide"
            @click.stop="(e) => showTip(e, d.hint)"
            @touchstart.passive="(e) => showTip(e, d.hint)"
          >
            <title v-if="d.hint">{{ d.hint }}</title>
          </rect>

          <text
            :x="PADDING.left - 10"
            :y="PADDING.top + i * (barHeight + barGap) + barHeight / 2 + 4"
            text-anchor="end"
            class="text-xs fill-gray-700 font-medium pointer-events-none"
          >
            {{ d.label.length > 18 ? d.label.slice(0, 16) + '…' : d.label }}
          </text>

          <rect
            :x="PADDING.left"
            :y="PADDING.top + i * (barHeight + barGap)"
            :width="WIDTH - PADDING.left - PADDING.right"
            :height="barHeight"
            fill="#f3f4f6"
            rx="4"
            class="pointer-events-none"
          />

          <rect
            :x="PADDING.left"
            :y="PADDING.top + i * (barHeight + barGap)"
            :width="toX(d.value) - PADDING.left"
            :height="barHeight"
            :fill="d.color || '#0f766e'"
            rx="4"
            class="pointer-events-none"
          />

          <text
            :x="toX(d.value) + 6"
            :y="PADDING.top + i * (barHeight + barGap) + barHeight / 2 + 4"
            class="text-xs fill-gray-600 font-semibold pointer-events-none"
          >
            {{ d.value }}
          </text>
        </template>
      </g>
    </svg>

    <div
      v-if="tip"
      class="pointer-events-none absolute z-20 max-w-[240px] -translate-y-full rounded-lg bg-gray-900 px-3 py-2 text-xs leading-snug text-white shadow-lg"
      :style="{ left: `${tip.x}px`, top: `${tip.y}px`, transform: 'translate(-20%, -110%)' }"
    >
      {{ tip.text }}
    </div>
  </div>
</template>

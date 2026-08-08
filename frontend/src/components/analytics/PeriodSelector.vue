<script setup lang="ts">
import type { AnalyticsPeriod } from '../../types/analytics';

const props = defineProps<{
  modelValue: AnalyticsPeriod;
}>();

const emit = defineEmits<{
  (e: 'update:modelValue', value: AnalyticsPeriod): void;
}>();

const options: { value: AnalyticsPeriod; label: string }[] = [
  { value: '7d', label: '7 дней' },
  { value: '30d', label: '30 дней' },
  { value: '90d', label: '90 дней' },
];
</script>

<template>
  <div class="inline-flex bg-gray-100 rounded-lg p-1 gap-1">
    <button
      v-for="opt in options"
      :key="opt.value"
      @click="emit('update:modelValue', opt.value)"
      :class="[
        'px-4 py-1.5 rounded-md text-sm font-medium transition-colors',
        modelValue === opt.value
          ? 'bg-white text-primary shadow-sm'
          : 'text-gray-600 hover:text-gray-900'
      ]"
    >
      {{ opt.label }}
    </button>
  </div>
</template>
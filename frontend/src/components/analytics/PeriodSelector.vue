<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';
import type { AnalyticsPeriod } from '../../types/analytics';

const props = defineProps<{
  modelValue: AnalyticsPeriod;
}>();

const emit = defineEmits<{
  (e: 'update:modelValue', value: AnalyticsPeriod): void;
}>();

const { t } = useI18n();

const options = computed(() => [
  { value: '7d' as AnalyticsPeriod, label: t('analytics.period7d') },
  { value: '30d' as AnalyticsPeriod, label: t('analytics.period30d') },
  { value: '90d' as AnalyticsPeriod, label: t('analytics.period90d') },
]);
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

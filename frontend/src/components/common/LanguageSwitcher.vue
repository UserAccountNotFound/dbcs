<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import { setLocale, type AppLocale } from '../../i18n';

defineProps<{
  compact?: boolean;
}>();

const { locale, t } = useI18n();

const options: { value: AppLocale; label: string }[] = [
  { value: 'ru', label: 'RU' },
  { value: 'en', label: 'EN' },
];

function switchLocale(next: AppLocale) {
  if (locale.value === next) return;
  setLocale(next);
}
</script>

<template>
  <div
    class="inline-flex items-center gap-1 rounded-lg border border-gray-200 bg-white p-0.5"
    :class="compact ? 'text-xs' : 'text-sm'"
    role="group"
    :aria-label="t('common.language')"
  >
    <button
      v-for="opt in options"
      :key="opt.value"
      type="button"
      class="rounded-md px-2.5 py-1 font-medium transition-colors"
      :class="locale === opt.value
        ? 'bg-primary text-white shadow-sm'
        : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'"
      :aria-pressed="locale === opt.value"
      @click="switchLocale(opt.value)"
    >
      {{ opt.label }}
    </button>
  </div>
</template>

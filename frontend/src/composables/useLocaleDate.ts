import { computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { localeToBcp47, type AppLocale } from '../i18n';

export function useLocaleDate() {
  const { locale } = useI18n();

  const bcp47 = computed(() => localeToBcp47(locale.value as AppLocale));

  function formatDateTime(value: string | Date | null | undefined): string {
    if (value == null || value === '') return '—';
    try {
      const date = typeof value === 'string'
        ? new Date(value.endsWith('Z') ? value : `${value}Z`)
        : value;
      return date.toLocaleString(bcp47.value);
    } catch {
      return String(value);
    }
  }

  function formatDate(value: string | Date): string {
    const date = typeof value === 'string' ? new Date(value) : value;
    return date.toLocaleDateString(bcp47.value, { day: 'numeric', month: 'short' });
  }

  return { bcp47, formatDateTime, formatDate };
}

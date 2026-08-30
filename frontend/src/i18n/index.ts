import { createI18n } from 'vue-i18n';
import ru from './locales/ru';
import en from './locales/en';

export const LOCALE_STORAGE_KEY = 'dbcs-locale';
export const SUPPORTED_LOCALES = ['ru', 'en'] as const;
export type AppLocale = (typeof SUPPORTED_LOCALES)[number];

function readStoredLocale(): AppLocale {
  try {
    const saved = localStorage.getItem(LOCALE_STORAGE_KEY);
    if (saved && SUPPORTED_LOCALES.includes(saved as AppLocale)) {
      return saved as AppLocale;
    }
  } catch {
    /* ignore */
  }
  return 'ru';
}

const initialLocale = readStoredLocale();

export const i18n = createI18n({
  legacy: false,
  locale: initialLocale,
  fallbackLocale: 'en',
  messages: { ru, en },
});

export function setLocale(locale: AppLocale): void {
  i18n.global.locale.value = locale;
  try {
    localStorage.setItem(LOCALE_STORAGE_KEY, locale);
  } catch {
    /* ignore */
  }
  document.documentElement.lang = locale;
}

document.documentElement.lang = initialLocale;

export function localeToBcp47(locale: AppLocale): string {
  return locale === 'ru' ? 'ru-RU' : 'en-US';
}

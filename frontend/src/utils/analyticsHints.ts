import { i18n } from '../i18n';

const REFERRER_KEYS = [
  'Direct', 'Google', 'Yandex', 'Bing', 'DuckDuckGo',
  'Telegram', 'WhatsApp', 'Facebook', 'Twitter', 'LinkedIn',
  'VK', 'Instagram', 'Reddit', 'Other',
] as const;

const DEVICE_KEYS = ['Desktop', 'Mobile', 'Tablet', 'Unknown'] as const;

export function referrerHint(label: string): string {
  if (REFERRER_KEYS.includes(label as typeof REFERRER_KEYS[number])) {
    return i18n.global.t(`analytics.referrerHints.${label}`);
  }
  return i18n.global.t('analytics.referrerHints.domain', { label });
}

export function deviceHint(label: string): string {
  if (DEVICE_KEYS.includes(label as typeof DEVICE_KEYS[number])) {
    return i18n.global.t(`analytics.deviceHints.${label}`);
  }
  return i18n.global.t('analytics.deviceHints.generic', { label });
}

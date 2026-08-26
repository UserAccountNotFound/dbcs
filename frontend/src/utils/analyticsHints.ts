/** Краткие описания обозначений аналитики (источники и устройства). */

const REFERRER_HINTS: Record<string, string> = {
  Direct:
    'Прямой заход: ссылка введена вручную, из закладок, QR-кода или мессенджера без передаваемого источника перехода.',
  Google: 'Переход из поиска или сервисов Google.',
  Yandex: 'Переход из поиска или сервисов Яндекса.',
  Bing: 'Переход из поиска Bing.',
  DuckDuckGo: 'Переход из поиска DuckDuckGo.',
  Telegram: 'Переход из Telegram (ссылка или встроенный браузер).',
  WhatsApp: 'Переход из WhatsApp.',
  Facebook: 'Переход из Facebook.',
  Twitter: 'Переход из Twitter / X.',
  LinkedIn: 'Переход из LinkedIn.',
  VK: 'Переход из ВКонтакте.',
  Instagram: 'Переход из Instagram.',
  Reddit: 'Переход из Reddit.',
  Other: 'Источник распознан, но не относится к известным сервисам.',
};

const DEVICE_HINTS: Record<string, string> = {
  Desktop: 'Компьютер или ноутбук (по User-Agent браузера).',
  Mobile: 'Смартфон (по User-Agent браузера).',
  Tablet: 'Планшет (по User-Agent браузера).',
  Unknown: 'Тип устройства определить не удалось.',
};

export function referrerHint(label: string): string {
  if (REFERRER_HINTS[label]) return REFERRER_HINTS[label];
  return `Переходы с сайта «${label}» (домен из адреса источника).`;
}

export function deviceHint(label: string): string {
  if (DEVICE_HINTS[label]) return DEVICE_HINTS[label];
  return `Устройство: ${label}.`;
}

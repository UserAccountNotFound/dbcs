/**
 * Сборка deep-link / URL для мессенджеров из пользовательского ввода.
 */

/** Разрешённые схемы для абсолютных ссылок (без javascript:, data: и т.п.). */
const ALLOWED_SCHEMES = new Set([
  'http:',
  'https:',
  'viber:',
  'tg:',
  'telegram:',
  'whatsapp:',
]);

function asAllowedAbsoluteUrl(value: string): string | null {
  const v = value.trim();
  if (!v) return null;
  if (v.startsWith('//')) return `https:${v}`;

  const match = /^([a-z][a-z0-9+.-]*:)/i.exec(v);
  if (match) {
    const scheme = match[1].toLowerCase();
    if (!ALLOWED_SCHEMES.has(scheme)) return null;
    return v;
  }
  return null;
}

/** Безопасный href для поля website: только http(s). */
export function safeWebsiteHref(raw: string | null | undefined): string | null {
  if (!raw) return null;
  const v = raw.trim();
  if (!v) return null;
  if (/^https?:\/\//i.test(v)) return v;
  if (/^[a-z][a-z0-9+.-]*:/i.test(v)) return null;
  return `https://${v}`;
}

function stripAt(value: string): string {
  return value.replace(/^@+/, '').trim();
}

function digitsOnly(value: string): string {
  return value.replace(/\D/g, '');
}

export type MessengerKind =
  | 'telegram'
  | 'whatsapp'
  | 'viber'
  | 'wechat'
  | 'messenger_max'
  | 'discord'
  | 'vk';

export function buildMessengerHref(kind: MessengerKind, raw: string): string | null {
  const value = raw.trim();
  if (!value) return null;

  const existing = asAllowedAbsoluteUrl(value);
  if (existing) return existing;

  switch (kind) {
    case 'telegram': {
      const u = stripAt(value);
      if (u.startsWith('t.me/')) return `https://${u}`;
      return `https://t.me/${u}`;
    }
    case 'whatsapp': {
      const digits = digitsOnly(value);
      return digits ? `https://wa.me/${digits}` : null;
    }
    case 'viber': {
      const digits = digitsOnly(value);
      if (digits.length >= 7) {
        return `viber://chat?number=%2B${digits}`;
      }
      return null;
    }
    case 'wechat':
      return null;
    case 'messenger_max': {
      const u = stripAt(value);
      if (u.includes('max.ru')) return `https://${u.replace(/^https?:\/\//i, '')}`;
      return `https://max.ru/${u}`;
    }
    case 'discord': {
      const u = value.trim();
      if (u.includes('discord.gg') || u.includes('discord.com')) {
        if (/^https?:\/\//i.test(u)) return u;
        if (/^[a-z][a-z0-9+.-]*:/i.test(u)) return null;
        return `https://${u}`;
      }
      return null;
    }
    case 'vk': {
      const u = stripAt(value);
      if (u.includes('vk.com') || u.includes('vk.ru')) {
        return `https://${u.replace(/^https?:\/\//i, '')}`;
      }
      return `https://vk.com/${u}`;
    }
    default:
      return null;
  }
}

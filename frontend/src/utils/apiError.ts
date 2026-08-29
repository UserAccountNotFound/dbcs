import { i18n } from '../i18n';

export function formatApiDetail(detail: unknown, fallback?: string): string {
  const fb = fallback ?? i18n.global.t('errors.generic');
  if (detail == null) return fb;

  if (typeof detail === 'string') return detail;

  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => {
        if (typeof item === 'string') return item;
        if (item && typeof item === 'object' && 'msg' in item) {
          return String((item as { msg: unknown }).msg);
        }
        return null;
      })
      .filter(Boolean);

    return messages.length > 0 ? messages.join('; ') : fb;
  }

  if (typeof detail === 'object' && detail !== null && 'msg' in detail) {
    return String((detail as { msg: unknown }).msg);
  }

  return fb;
}

export function getAxiosErrorMessage(error: unknown, fallback?: string): string {
  const detail = (error as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
  return formatApiDetail(detail, fallback);
}

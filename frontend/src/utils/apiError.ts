export function formatApiDetail(detail: unknown, fallback = 'Произошла ошибка'): string {
  if (detail == null) return fallback;

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

    return messages.length > 0 ? messages.join('; ') : fallback;
  }

  if (typeof detail === 'object' && detail !== null && 'msg' in detail) {
    return String((detail as { msg: unknown }).msg);
  }

  return fallback;
}

export function getAxiosErrorMessage(error: unknown, fallback = 'Произошла ошибка'): string {
  const detail = (error as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
  return formatApiDetail(detail, fallback);
}

export function normalizeApiError(error, fallback = 'Request failed') {
  const detail = error?.response?.data?.detail;

  if (typeof detail === 'string') return detail;

  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => {
        if (!item || typeof item !== 'object') return String(item);

        const field = Array.isArray(item.loc) ? item.loc.slice(1).join('.') : '';
        const prefix = field ? `${field}: ` : '';
        return `${prefix}${item.msg || 'Invalid value'}`;
      })
      .filter(Boolean);

    if (messages.length > 0) return messages.join('; ');
  }

  if (typeof error?.response?.data?.message === 'string') {
    return error.response.data.message;
  }

  if (typeof error?.message === 'string' && error.message.trim()) {
    return error.message;
  }

  return fallback;
}
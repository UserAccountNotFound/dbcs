import apiClient from './client';
import type { PublicCard } from '../types/publicCard';

const PUBLIC_CARDS_ENDPOINT = '/public/cards';

export const publicCardApi = {
  async getPublicCard(slug: string): Promise<PublicCard> {
    // Передаём document.referrer — реальный внешний источник перехода на страницу визитки.
    // Обычный HTTP Referer на /api/... указывает на саму SPA-страницу и для аналитики бесполезен.
    const originalReferrer =
      typeof document !== 'undefined' ? document.referrer || '' : '';

    const { data } = await apiClient.get(`${PUBLIC_CARDS_ENDPOINT}/${slug}`, {
      headers: {
        'X-DBCS-Referrer': originalReferrer,
      },
    });
    return data;
  },

  // Публичные endpoints не требуют JWT, поэтому можно использовать прямые URL
  getVCardUrl(slug: string): string {
    return `${import.meta.env.VITE_API_BASE_URL}${PUBLIC_CARDS_ENDPOINT}/${slug}/vcard.vcf`;
  },

  getQrCodeUrl(slug: string): string {
    return `${import.meta.env.VITE_API_BASE_URL}${PUBLIC_CARDS_ENDPOINT}/${slug}/qrcode.svg`;
  }
};
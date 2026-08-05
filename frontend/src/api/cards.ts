import apiClient from './client';
import type { Card, CardListResponse, CardCreatePayload, CardUpdatePayload } from '../types/card';
import type { CardStats } from '../types/stats';

const CARDS_ENDPOINT = '/cards';

export const cardApi = {
  async getCards(limit = 20, offset = 0): Promise<CardListResponse> {
    const { data } = await apiClient.get(CARDS_ENDPOINT, { params: { limit, offset } });
    return data;
  },

  async getCard(cardId: string): Promise<Card> {
    const { data } = await apiClient.get(`${CARDS_ENDPOINT}/${cardId}`);
    return data;
  },

  async createCard(payload: CardCreatePayload): Promise<Card> {
    const { data } = await apiClient.post(CARDS_ENDPOINT, payload);
    return data;
  },

  async updateCard(cardId: string, payload: CardUpdatePayload): Promise<Card> {
    const { data } = await apiClient.patch(`${CARDS_ENDPOINT}/${cardId}`, payload);
    return data;
  },

  async deleteCard(cardId: string): Promise<void> {
    await apiClient.delete(`${CARDS_ENDPOINT}/${cardId}`);
  },

  async regenerateSlug(cardId: string): Promise<Card> {
    const { data } = await apiClient.post(`${CARDS_ENDPOINT}/${cardId}/regenerate-slug`);
    return data;
  },

  // Статистика карточки
  async getCardStats(cardId: string): Promise<CardStats> {
    const { data } = await apiClient.get(`${CARDS_ENDPOINT}/${cardId}/stats`);
    return data;
  },

  async getQrCodeBlob(cardId: string): Promise<Blob> {
    const { data } = await apiClient.get(`${CARDS_ENDPOINT}/${cardId}/qrcode.svg`, {
      responseType: 'blob'
    });
    return data;
  },

  async getVCardBlob(cardId: string): Promise<Blob> {
    const { data } = await apiClient.get(`${CARDS_ENDPOINT}/${cardId}/vcard.vcf`, {
      responseType: 'blob'
    });
    return data;
  }
};
import apiClient from './client';
import type {
  AdminUserListResponse,
  AdminUserCreate,
  AdminUserUpdate,
  AdminUser,
  AdminCardListResponse,
  AuditLogListResponse,
  OverviewStats,
} from '../types/admin';

const ADMIN_ENDPOINT = '/admin';

export const adminApi = {
    async createUser(payload: AdminUserCreate): Promise<AdminUser> {
    const { data } = await apiClient.post(`${ADMIN_ENDPOINT}/users`, payload);
    return data;
  },

  async deleteUser(userId: string): Promise<void> {
    await apiClient.delete(`${ADMIN_ENDPOINT}/users/${userId}`);
  },
  
  async getUsers(limit = 20, offset = 0, search?: string): Promise<AdminUserListResponse> {
    const { data } = await apiClient.get(`${ADMIN_ENDPOINT}/users`, {
      params: { limit, offset, search: search || undefined },
    });
    return data;
  },

  async updateUser(userId: string, payload: AdminUserUpdate): Promise<AdminUser> {
    const { data } = await apiClient.patch(`${ADMIN_ENDPOINT}/users/${userId}`, payload);
    return data;
  },

  async getCards(limit = 20, offset = 0, search?: string): Promise<AdminCardListResponse> {
    const { data } = await apiClient.get(`${ADMIN_ENDPOINT}/cards`, {
      params: { limit, offset, search: search || undefined },
    });
    return data;
  },

  async deactivateCard(cardId: string): Promise<void> {
    await apiClient.post(`${ADMIN_ENDPOINT}/cards/${cardId}/deactivate`);
  },

  async getAuditLogs(limit = 50, offset = 0, action?: string): Promise<AuditLogListResponse> {
    const { data } = await apiClient.get(`${ADMIN_ENDPOINT}/audit`, {
      params: { limit, offset, action: action || undefined },
    });
    return data;
  },

  async getOverviewStats(): Promise<OverviewStats> {
    const { data } = await apiClient.get(`${ADMIN_ENDPOINT}/stats/overview`);
    return data;
  },
};
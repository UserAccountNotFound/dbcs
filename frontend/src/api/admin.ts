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

import type { 
  ExtendedAnalytics, 
  AnalyticsPeriod 
} from '../types/analytics';

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

  async getTemplates(limit = 20, offset = 0, search?: string) {
    const { data } = await apiClient.get(`${ADMIN_ENDPOINT}/templates`, {
      params: { limit, offset, search: search || undefined },
    });
    return data;
  },

  async createTemplate(payload: {
    code: string;
    name: string;
    description?: string | null;
    is_active?: boolean;
    meta?: {
      version?: number;
      effect?: string | null;
      default_accent?: string | null;
      default_scheme?: 'light' | 'dark' | null;
    };
  }): Promise<{ id: string; code: string; name: string; is_active: boolean }> {
    const { data } = await apiClient.post(`${ADMIN_ENDPOINT}/templates`, payload);
    return data;
  },

  async updateTemplate(templateId: string, payload: any) {
    const { data } = await apiClient.patch(`${ADMIN_ENDPOINT}/templates/${templateId}`, payload);
    return data;
  },

  async toggleTemplate(templateId: string) {
    const { data } = await apiClient.post(`${ADMIN_ENDPOINT}/templates/${templateId}/toggle-active`);
    return data;
  },

  async deleteTemplate(templateId: string) {
    await apiClient.delete(`${ADMIN_ENDPOINT}/templates/${templateId}`);
  },

  async uploadTemplateCss(templateId: string, file: File) {
    const form = new FormData();
    form.append('file', file);
    const { data } = await apiClient.post(
      `${ADMIN_ENDPOINT}/templates/${templateId}/css`,
      form,
      { headers: { 'Content-Type': 'multipart/form-data' } },
    );
    return data;
  },

  async getExtendedAnalytics(period: AnalyticsPeriod = '30d'): Promise<ExtendedAnalytics> {
    const { data } = await apiClient.get(`${ADMIN_ENDPOINT}/analytics/extended`, {
      params: { period },
    });
    return data;
  },
};
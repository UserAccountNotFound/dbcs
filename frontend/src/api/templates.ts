import apiClient from './client';
import type { TemplateListResponse, Template } from '../types/template';

const TEMPLATES_ENDPOINT = '/templates';

export const templateApi = {
  async getTemplates(): Promise<TemplateListResponse> {
    const { data } = await apiClient.get(TEMPLATES_ENDPOINT);
    return data;
  },

  async getTemplate(templateId: string): Promise<Template> {
    const { data } = await apiClient.get(`${TEMPLATES_ENDPOINT}/${templateId}`);
    return data;
  },
};
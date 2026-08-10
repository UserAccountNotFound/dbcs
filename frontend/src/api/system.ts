import apiClient from './client';

export interface HealthResponse {
  status: string;
  environment: string;
  version: string;
}

export const systemApi = {
  async getHealth(): Promise<HealthResponse> {
    const { data } = await apiClient.get<HealthResponse>('/health');
    return data;
  },
};

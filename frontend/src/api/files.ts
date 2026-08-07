import apiClient from './client';

export interface FileResponse {
  id: string;
  original_name: string;
  mime_type: string;
  size_bytes: number;
  created_at: string;
}

export const fileApi = {
  async upload(file: File): Promise<FileResponse> {
    const formData = new FormData();
    formData.append('file', file);
    
    const { data } = await apiClient.post('/files/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    
    return data;
  },

  async delete(fileId: string): Promise<void> {
    await apiClient.delete(`/files/${fileId}`);
  },

  getFileUrl(fileId: string): string {
    return `${import.meta.env.VITE_API_BASE_URL}/files/${fileId}`;
  },
};
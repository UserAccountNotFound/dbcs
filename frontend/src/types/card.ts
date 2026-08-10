export interface CardTheme {
  color_scheme: 'light' | 'dark';
  layout: 'classic' | 'modern' | 'compact' | 'corporate' | 'creative';
  font: 'inter' | 'roboto' | 'open_sans';
  accent_color: string;
  show_photo: boolean;
  show_qr: boolean;
}

export interface Card {
  id: string;
  slug: string;
  title: string;
  full_name: string;
  job_title: string | null;
  department: string | null;
  company: string | null;
  phone: string | null;
  phone_additional: string | null;
  telegram: string | null;
  whatsapp: string | null;
  viber: string | null;
  wechat: string | null;
  messenger_max: string | null;
  discord: string | null;
  vk: string | null;
  email: string | null;
  website: string | null;
  address: string | null;
  note: string | null;
  avatar_file_id: string | null;
  logo_file_id: string | null;
  theme: CardTheme;
  template_id: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  public_url: string;
}

export interface CardListResponse {
  items: Card[];
  total: number;
  limit: number;
  offset: number;
}

export interface CardCreatePayload {
  title: string;
  full_name: string;
  job_title?: string | null;
  department?: string | null;
  company?: string | null;
  phone?: string | null;
  phone_additional?: string | null;
  telegram?: string | null;
  whatsapp?: string | null;
  viber?: string | null;
  wechat?: string | null;
  messenger_max?: string | null;
  discord?: string | null;
  vk?: string | null;
  email?: string | null;
  website?: string | null;
  address?: string | null;
  note?: string | null;
  avatar_file_id: string | null;
  logo_file_id: string | null;
  template_id: string | null;
  theme: CardTheme;
}

export interface CardUpdatePayload extends Partial<CardCreatePayload> {
  is_active?: boolean;
}

export interface AdminUser {
  id: string;
  email: string;
  full_name: string;
  role: 'USER' | 'ADMIN' | 'SUPERADMIN';
  is_active: boolean;
  mfa_enabled: boolean;
  created_at: string;
  last_login_at: string | null;
  cards_count: number;
}

export interface AdminUserCreate {
  email: string;
  full_name: string;
  password: string;
  role: 'USER' | 'ADMIN' | 'SUPERADMIN';
}

export interface AdminUserListResponse {
  items: AdminUser[];
  total: number;
  limit: number;
  offset: number;
}

export interface AdminUserUpdate {
  email?: string;
  full_name?: string;
  role?: 'USER' | 'ADMIN' | 'SUPERADMIN';
  is_active?: boolean;
  password?: string;  // Cмена пароля при редактировании
}

export interface AdminCard {
  id: string;
  slug: string;
  title: string;
  full_name: string;
  is_active: boolean;
  created_at: string;
  user_email: string;
  visits_count: number;
}

export interface AdminCardListResponse {
  items: AdminCard[];
  total: number;
  limit: number;
  offset: number;
}

export interface AuditLog {
  id: number;
  action: string;
  entity_type: string | null;
  entity_id: string | null;
  created_at: string;
  actor_email: string | null;
  details: Record<string, any> | null;
}

export interface AuditLogListResponse {
  items: AuditLog[];
  total: number;
  limit: number;
  offset: number;
}

export interface OverviewStats {
  total_users: number;
  active_users: number;
  total_cards: number;
  active_cards: number;
  total_visits: number;
  total_vcard_downloads: number;
}

// Реэкспорт типов шаблонов для использования в админке
export type { AdminTemplate, TemplateSchema, Template } from './template';
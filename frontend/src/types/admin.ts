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


export type BackupSchedule = 'off' | 'hourly' | 'daily' | 'weekly';

export interface BackupSettings {
  storage_path: string;
  schedule: BackupSchedule;
  schedule_hour: number;
  schedule_weekday: number;
  retention_count: number;
  enabled: boolean;
  last_run_at: string | null;
  last_status: string | null;
  last_message: string | null;
  last_backup_file: string | null;
  updated_at: string;
}

export interface BackupSettingsUpdate {
  storage_path?: string;
  schedule?: BackupSchedule;
  schedule_hour?: number;
  schedule_weekday?: number;
  retention_count?: number;
  enabled?: boolean;
}

export interface BackupFile {
  filename: string;
  size_bytes: number;
  created_at: string;
}

export interface BackupListResponse {
  items: BackupFile[];
}

export interface BackupRunResponse {
  filename: string;
  size_bytes: number;
  created_at: string;
  detail: string;
}

export interface BackupRestoreResponse {
  detail: string;
}


export interface SmtpSettings {
  enabled: boolean;
  host: string;
  port: number;
  use_tls: boolean;
  use_ssl: boolean;
  username: string;
  from_email: string;
  from_name: string;
  password_set: boolean;
  updated_at: string;
}

export interface SmtpTestRequest {
  to_email?: string;
  host?: string;
  port?: number;
  use_tls?: boolean;
  use_ssl?: boolean;
  username?: string;
  password?: string;
  from_email?: string;
  from_name?: string;
}

export interface SmtpTestResponse {
  detail: string;
}

export interface SmtpSettingsUpdate {
  enabled?: boolean;
  host?: string;
  port?: number;
  use_tls?: boolean;
  use_ssl?: boolean;
  username?: string;
  password?: string;
  from_email?: string;
  from_name?: string;
}

export interface DocsSettings {
  docs_enabled: boolean;
  redoc_enabled: boolean;
  updated_at: string;
}

export interface DocsSettingsUpdate {
  docs_enabled?: boolean;
  redoc_enabled?: boolean;
}

// Реэкспорт типов шаблонов для использования в админке
export type { AdminTemplate, TemplateMeta, TemplateSchema, Template } from './template';
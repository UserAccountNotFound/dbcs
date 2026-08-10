export interface TemplateMeta {
  version?: number;
  effect?: 'polygon' | null;
  default_accent?: string | null;
  default_scheme?: 'light' | 'dark' | null;
}

/** @deprecated используйте TemplateMeta */
export type TemplateSchema = TemplateMeta;

export interface Template {
  id: string;
  code: string;
  name: string;
  description: string | null;
  preview_image: string | null;
  is_active: boolean;
  created_at: string;
  css_url: string | null;
  has_css: boolean;
  meta: TemplateMeta | null;
  schema_data?: TemplateMeta | null;
}

export interface TemplateListResponse {
  items: Template[];
  total: number;
}

export interface AdminTemplate extends Template {
  updated_at: string;
  cards_count: number;
}

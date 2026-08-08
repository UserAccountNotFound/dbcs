export interface TemplateSchema {
  primary_color: string;
  secondary_color: string;
  text_color: string;
  heading_font: string;
  body_font: string;
  layout_type: 'classic' | 'modern' | 'compact' | 'corporate' | 'creative';
  show_photo: boolean;
  show_qr: boolean;
  show_logo: boolean;
  photo_position: 'left' | 'top' | 'right';
  border_radius: number;
  shadow: boolean;
  gradient_header: boolean;
}

export interface Template {
  id: string;
  code: string;
  name: string;
  description: string | null;
  preview_image: string | null;
  is_active: boolean;
  created_at: string;
  schema_data: TemplateSchema | null;
}

export interface TemplateListResponse {
  items: Template[];
  total: number;
}

export interface AdminTemplate extends Template {
  updated_at: string;
  cards_count: number;
}
import type { CardTheme } from './card';

export interface PublicCard {
  slug: string;
  title: string;
  full_name: string;
  job_title: string | null;
  department: string | null;
  company: string | null;
  phone: string | null;
  email: string | null;
  website: string | null;
  address: string | null;
  note: string | null;

  theme: CardTheme;
  template_code: string | null;
  css_url: string | null;
  template_effect: string | null;

  avatar_url: string | null;
  logo_url: string | null;

  public_url: string;
}

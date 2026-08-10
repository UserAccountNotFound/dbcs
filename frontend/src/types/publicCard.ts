import type { CardTheme } from './card';

export interface PublicCard {
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

  theme: CardTheme;
  template_code: string | null;
  css_url: string | null;
  template_effect: string | null;

  avatar_url: string | null;
  logo_url: string | null;

  public_url: string;
}

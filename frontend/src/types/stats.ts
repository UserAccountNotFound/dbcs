export interface DailyStat {
  date: string; // ISO формат: "2026-08-01"
  views: number;
  vcard_downloads: number;
}

export interface CardStats {
  total_views: number;
  total_vcard_downloads: number;
  views_last_30_days: number;
  vcard_downloads_last_30_days: number;
  daily: DailyStat[];
}
export type AnalyticsPeriod = '7d' | '30d' | '90d';

export interface TimeSeriesPoint {
  date: string;  // ISO: "2026-08-01"
  views: number;
  downloads: number;
}

export interface TopCard {
  id: string;
  title: string;
  full_name: string;
  slug: string;
  user_email: string;
  views: number;
  downloads: number;
}

export interface TopUser {
  id: string;
  email: string;
  full_name: string;
  cards_count: number;
  views: number;
  downloads: number;
}

export interface ReferrerStat {
  source: string;
  count: number;
}

export interface DeviceStat {
  device: 'Desktop' | 'Mobile' | 'Tablet' | 'Unknown';
  count: number;
}

export interface HeatmapCell {
  day_of_week: number;  // 0=Пн, 6=Вс
  hour: number;         // 0-23
  count: number;
}

export interface ExtendedAnalytics {
  period: AnalyticsPeriod;
  generated_at: string;
  time_series: TimeSeriesPoint[];
  top_cards: TopCard[];
  top_users: TopUser[];
  referrers: ReferrerStat[];
  devices: DeviceStat[];
  hourly_heatmap: HeatmapCell[];
}
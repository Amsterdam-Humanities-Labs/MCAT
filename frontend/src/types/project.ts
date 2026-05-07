export type Platform = 'youtube' | 'instagram' | 'facebook' | 'twitter';

export type RunStatus = 'in_progress' | 'completed' | 'abandoned';

export interface RunStatusSummary {
  live: number;
  removed: number;
  restricted: number;
  error: number;
}

export interface RunChangesSummary {
  [transition: string]: number; // e.g. "live_to_removed": 3
}

export interface Run {
  id: string;
  started_at: string;
  completed_at: string | null;
  status: RunStatus;
  screenshots_enabled: boolean;
  run_type: string;
  is_baseline: boolean;
  duration_seconds: number;
  total_checked: number;
  changes_count: number;
  changes_summary: RunChangesSummary;
  status_summary: RunStatusSummary;
}

export interface TrackingConfig {
  enabled: boolean;
  interval_value: number;
  interval_unit: 'minutes' | 'hours' | 'days';
  last_check: string | null;
  next_check: string | null;
}

export interface AuthInfo {
  has_cookies: boolean;
  username: string;
  captured_at: string | null;
}

export interface Project {
  name: string;
  platform: Platform;
  path: string;
  mtime?: number;
  url_count: number;
  url_column: string;
  screenshots_enabled: boolean;
  runs: Run[];
  tracking: TrackingConfig;
  auth?: AuthInfo;
}

export interface CreateProjectRequest {
  name: string;
  platform: Platform;
  location: string;
  csv_path: string;
  url_column: string;
}

export type Platform = 'youtube' | 'instagram';

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
  startedAt: string;
  completedAt: string | null;
  status: RunStatus;
  screenshotsEnabled: boolean;
  runType: string;
  isBaseline: boolean;
  durationSeconds: number;
  totalChecked: number;
  changesCount: number;
  changesSummary: RunChangesSummary;
  statusSummary: RunStatusSummary;
}

export interface TrackingConfig {
  enabled: boolean;
  intervalValue: number;
  intervalUnit: 'minutes' | 'hours' | 'days';
  lastCheck: string | null;
  nextCheck: string | null;
}

export interface Project {
  name: string;
  platform: Platform;
  path: string;
  mtime?: number;
  urlCount: number;
  urlColumn: string;
  runs: Run[];
  tracking: TrackingConfig;
}

export interface CreateProjectRequest {
  name: string;
  platform: Platform;
  location: string;
  csvPath: string;
  urlColumn: string;
  preserveColumns?: string[];
}

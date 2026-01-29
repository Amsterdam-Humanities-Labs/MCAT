export type Platform = 'youtube' | 'instagram';

export type RunStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';

export interface Run {
  id: string;
  status: RunStatus;
  startedAt: string | null;
  completedAt: string | null;
}

export interface Project {
  name: string;
  platform: Platform;
  path: string;
  combinedCsvPath: string;
  urlCount: number;
  urlColumn: string;
  runs: Run[];
}

export interface CreateProjectRequest {
  name: string;
  platform: Platform;
  location: string;
  csvPath: string;
  urlColumn: string;
  preserveColumns?: string[];
}

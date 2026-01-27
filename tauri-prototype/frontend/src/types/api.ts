export interface ApiResponse<T = unknown> {
  success?: boolean;
  error?: string;
  data?: T;
}

export interface HealthResponse {
  status: 'ok' | 'error';
  hasProject: boolean;
  isProcessing: boolean;
}

export interface ProjectStatusResponse {
  project: import('./project').Project | null;
}

export interface ProcessStatusResponse {
  state: import('./processing').ProcessingState;
  total: number;
  processed: number;
  stats: import('./processing').ProcessingStats;
  action: string;
  error: string | null;
}

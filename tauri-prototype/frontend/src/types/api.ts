export interface HealthResponse {
  status: 'ok' | 'error';
  hasProject: boolean;
  isProcessing: boolean;
}

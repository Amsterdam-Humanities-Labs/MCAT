import type {
  HealthResponse,
  CreateProjectRequest,
  StartProcessingRequest,
  CsvInfo,
  ImportPreview,
} from '../../types';

interface InterruptedRun {
  run_id: string;
  processed: number;
  total: number;
  remaining: number;
}

let backendUrl = '';

export function setBackendUrl(url: string) {
  backendUrl = url;
}

export function getBackendUrl(): string {
  return backendUrl;
}

async function callBackend<T>(
  endpoint: string,
  method: 'GET' | 'POST' = 'GET',
  body?: unknown,
  retries = 3
): Promise<T> {
  let lastError: Error | null = null;

  for (let i = 0; i < retries; i++) {
    try {
      const opts: RequestInit = { method };
      if (method === 'POST') {
        opts.headers = { 'Content-Type': 'application/json' };
        opts.body = JSON.stringify(body ?? {});
      }
      const response = await fetch(`${backendUrl}${endpoint}`, opts);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${await response.text()}`);
      }
      return await response.json() as T;
    } catch (e) {
      lastError = e as Error;
      if (i < retries - 1) {
        await new Promise(r => setTimeout(r, 500 * (i + 1)));
      }
    }
  }

  throw lastError;
}

export const api = {
  // Health
  health: () => callBackend<HealthResponse>('/health'),

  // Project
  createProject: (data: CreateProjectRequest) =>
    callBackend<{ success: boolean; project_path?: string }>('/project/create', 'POST', data),
  openProject: (path: string) =>
    callBackend<{ success: boolean; name?: string }>('/project/open', 'POST', { path }),
  closeProject: () =>
    callBackend<{ success: boolean }>('/project/close', 'POST'),

  // Processing
  startProcessing: (data?: StartProcessingRequest) =>
    callBackend<{ success: boolean }>('/process/start', 'POST', data ?? {}),
  pauseProcessing: () =>
    callBackend<{ success: boolean }>('/process/pause', 'POST'),
  resumeProcessing: () =>
    callBackend<{ success: boolean }>('/process/resume', 'POST'),
  cancelProcessing: () =>
    callBackend<{ success: boolean }>('/process/cancel', 'POST'),

  // Runs
  resumeRun: (run_id: string) =>
    callBackend<{ success: boolean; remaining_urls: number }>('/run/resume', 'POST', { run_id }),
  abandonRun: (run_id: string) =>
    callBackend<{ success: boolean }>('/run/abandon', 'POST', { run_id }),
  getInterruptedRun: () =>
    callBackend<{ has_interrupted: boolean; run?: InterruptedRun }>('/run/interrupted'),

  // CSV Operations
  loadCsv: (path: string) =>
    callBackend<CsvInfo>('/csv/load', 'POST', { path }),
  detectUrlColumn: (columns: string[]) =>
    callBackend<{ candidates: string[]; recommended: string | null }>('/csv/detect-url-column', 'POST', { columns }),

  // Import
  previewImport: (csv_path: string) =>
    callBackend<ImportPreview>('/project/import-preview', 'POST', { csv_path }),
  confirmImport: () =>
    callBackend<{ added: number }>('/project/import-confirm', 'POST'),

  // Tracking
  startTracking: (interval_value: number, interval_unit: string = 'minutes') =>
    callBackend<{ enabled: boolean; interval_value: number; interval_unit: string; next_check: string }>(
      '/tracking/start',
      'POST',
      { interval_value, interval_unit }
    ),

  // Dialogs (served by Python backend)
  pickFile: (filters?: Array<{ name: string; extensions: string[] }>) =>
    callBackend<{ path: string | null }>('/dialog/open-file', 'POST', { filters }),
  pickFolder: () =>
    callBackend<{ path: string | null }>('/dialog/open-folder', 'POST'),
  openExternal: (url: string) =>
    callBackend<{ success: boolean }>('/dialog/open-external', 'POST', { url }),
};

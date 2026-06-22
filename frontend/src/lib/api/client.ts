import type {
  HealthResponse,
  CreateProjectRequest,
  StartProcessingRequest,
  CsvInfo,
  ImportPreview,
} from '../../types';
import type { Project } from '../../types/project';

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
    callBackend<{ success: boolean; project: Project }>('/project/create', 'POST', data),
  openProject: (path: string) =>
    callBackend<{ success: boolean; project: Project }>('/project/open', 'POST', { path }),
  closeProject: () =>
    callBackend<{ success: boolean }>('/project/close', 'POST'),
  setScreenshots: (enabled: boolean) =>
    callBackend<{ success: boolean; project: Project }>('/project/screenshots', 'POST', { enabled }),
  setTrackingConfig: (config: { enabled?: boolean; interval_value?: number; interval_unit?: string }) =>
    callBackend<{ success: boolean; project: Project }>('/project/tracking-config', 'POST', config),

  // Processing
  startProcessing: (data?: StartProcessingRequest) =>
    callBackend<{ success: boolean }>('/process/start', 'POST', data ?? {}),
  pauseProcessing: () =>
    callBackend<{ success: boolean }>('/process/pause', 'POST'),
  resumeProcessing: () =>
    callBackend<{ success: boolean }>('/process/resume', 'POST'),
  abandonProcessing: () =>
    callBackend<{ success: boolean }>('/process/abandon', 'POST'),
  // Run data
  getRunChangedResults: (run_id: string) =>
    callBackend<{ columns: string[]; rows: Record<string, unknown>[] }>(
      '/run/changed-results', 'POST', { run_id }
    ),
  getRunResults: (run_id: string) =>
    callBackend<{ columns: string[]; rows: Record<string, unknown>[] }>(
      '/run/results', 'POST', { run_id }
    ),

  // CSV Operations
  loadCsv: (path: string) =>
    callBackend<CsvInfo>('/csv/load', 'POST', { path }),
  detectUrlColumn: (columns: string[]) =>
    callBackend<{ candidates: string[]; recommended: string | null }>('/csv/detect-url-column', 'POST', { columns }),

  // Import
  previewImport: (csv_path: string) =>
    callBackend<ImportPreview>('/project/import-preview', 'POST', { csv_path }),
  confirmImport: () =>
    callBackend<{ added: number; project: Project }>('/project/import-confirm', 'POST'),

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

  // Auth
  startLogin: () =>
    callBackend<{ success: boolean; platform?: string; error?: string }>('/auth/start-login', 'POST'),
  logout: () =>
    callBackend<{ success: boolean; project?: Project }>('/auth/logout', 'POST'),
};

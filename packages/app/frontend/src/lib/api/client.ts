import type {
  HealthResponse,
  CreateProjectRequest,
  StartProcessingRequest,
  CsvInfo,
} from '../../types';
import type { Project } from '../../types/project';

let backendUrl = '';
let authToken = '';

export function setBackendUrl(url: string) {
  backendUrl = url;
}

export function getBackendUrl(): string {
  return backendUrl;
}

// Minted by the backend at startup and passed to the SPA in its URL. Sent on
// every API call; without it the backend answers 403.
export function setAuthToken(token: string) {
  authToken = token;
}

export function getAuthToken(): string {
  return authToken;
}

async function callBackend<T>(
  endpoint: string,
  method: 'GET' | 'POST' = 'GET',
  body?: unknown,
  retries = 3
): Promise<T> {
  // The token goes on GETs too — /health is gated like every other route.
  const headers: Record<string, string> = { 'X-MCAT-Token': authToken };
  if (method === 'POST') {
    headers['Content-Type'] = 'application/json';
  }
  const opts: RequestInit = { method, headers };
  if (method === 'POST') {
    opts.body = JSON.stringify(body ?? {});
  }

  let lastError: Error | null = null;
  for (let i = 0; i < retries; i++) {
    let response: Response;
    try {
      response = await fetch(`${backendUrl}${endpoint}`, opts);
    } catch (e) {
      // Network failure — retry with backoff.
      lastError = e as Error;
      if (i < retries - 1) {
        await new Promise(r => setTimeout(r, 500 * (i + 1)));
        continue;
      }
      throw lastError;
    }

    // Response received; an HTTP error is a final answer, not retried.
    if (!response.ok) {
      // A 403 with no token of our own is the one recoverable cause, and it is
      // otherwise indistinguishable from any other refusal. A 403 *with* a
      // token means something else, so it keeps the generic message.
      if (response.status === 403 && !authToken) {
        throw new Error('Lost the connection token for the backend — restart MCAT.');
      }
      let message = `Request failed (${response.status})`;
      try {
        const data = await response.json();
        if (data?.error) message = data.error;
      } catch {
        // non-JSON body — keep the generic message
      }
      throw new Error(message);
    }
    return await response.json() as T;
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

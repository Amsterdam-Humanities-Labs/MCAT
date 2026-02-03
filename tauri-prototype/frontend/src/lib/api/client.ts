import { invoke } from '@tauri-apps/api/core';
import type {
  HealthResponse,
  CreateProjectRequest,
  StartProcessingRequest,
  CsvInfo,
  ImportPreview,
  CombinedResults,
} from '../../types';

interface InterruptedRun {
  runId: string;
  processed: number;
  total: number;
  remaining: number;
}

/**
 * Convert snake_case keys to camelCase recursively.
 * Handles the API boundary between Python (snake_case) and TypeScript (camelCase).
 */
function snakeToCamel(obj: unknown): unknown {
  if (obj === null || obj === undefined) return obj;
  if (Array.isArray(obj)) return obj.map(snakeToCamel);
  if (typeof obj === 'object') {
    const result: Record<string, unknown> = {};
    for (const [key, value] of Object.entries(obj as Record<string, unknown>)) {
      const camelKey = key.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase());
      result[camelKey] = snakeToCamel(value);
    }
    return result;
  }
  return obj;
}

/**
 * Convert camelCase keys to snake_case recursively.
 * Used for sending requests to the Python backend.
 */
function camelToSnake(obj: unknown): unknown {
  if (obj === null || obj === undefined) return obj;
  if (Array.isArray(obj)) return obj.map(camelToSnake);
  if (typeof obj === 'object') {
    const result: Record<string, unknown> = {};
    for (const [key, value] of Object.entries(obj as Record<string, unknown>)) {
      const snakeKey = key.replace(/[A-Z]/g, (letter) => `_${letter.toLowerCase()}`);
      result[snakeKey] = camelToSnake(value);
    }
    return result;
  }
  return obj;
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
      const response = await invoke('call_backend', {
        endpoint,
        method,
        body: body ? JSON.stringify(camelToSnake(body)) : undefined,
      });
      const parsed = JSON.parse(response as string);
      return snakeToCamel(parsed) as T;
    } catch (e) {
      lastError = e as Error;
      // Wait before retry (exponential backoff)
      if (i < retries - 1) {
        await new Promise(r => setTimeout(r, 500 * (i + 1)));
      }
    }
  }

  throw lastError;
}

export const api = {
  // Backend port for SSE
  getPort: () => invoke<number>('get_backend_port'),

  // Health
  health: () => callBackend<HealthResponse>('/health'),

  // Project
  createProject: (data: CreateProjectRequest) =>
    callBackend<{ success: boolean; projectPath?: string }>('/project/create', 'POST', data),
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
  resumeRun: (runId: string) =>
    callBackend<{ success: boolean; remainingUrls: number }>('/run/resume', 'POST', { runId }),
  abandonRun: (runId: string) =>
    callBackend<{ success: boolean }>('/run/abandon', 'POST', { runId }),
  getInterruptedRun: () =>
    callBackend<{ hasInterrupted: boolean; run?: InterruptedRun }>('/run/interrupted'),

  // CSV Operations
  loadCsv: (path: string) =>
    callBackend<CsvInfo>('/csv/load', 'POST', { path }),
  detectUrlColumn: (columns: string[]) =>
    callBackend<{ candidates: string[]; recommended: string | null }>('/csv/detect-url-column', 'POST', { columns }),

  // Import
  previewImport: (csvPath: string) =>
    callBackend<ImportPreview>('/project/import-preview', 'POST', { csvPath }),
  confirmImport: () =>
    callBackend<{ added: number }>('/project/import-confirm', 'POST'),

  // Results
  getCombinedResults: () =>
    callBackend<CombinedResults>('/results/combined'),
};

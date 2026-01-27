import type { ProcessingState } from '../../types';
import type { StatusCounts } from '../../types/results';
import { api } from '../api/client';

interface ProcessingStatus {
  state: ProcessingState;
  total: number;
  processed: number;
  stats: Record<string, unknown>;
  action: string;
  error: string | null;
  currentUrl: string | null;
  statusCounts: StatusCounts;
}

const defaultStatusCounts: StatusCounts = {
  live: 0,
  removed: 0,
  restricted: 0,
  error: 0,
  pending: 0,
};

function createProcessingStore() {
  let status = $state<ProcessingStatus>({
    state: 'idle',
    total: 0,
    processed: 0,
    stats: {},
    action: '',
    error: null,
    currentUrl: null,
    statusCounts: { ...defaultStatusCounts },
  });

  let storeError = $state<string | null>(null);

  return {
    get state() {
      return status.state;
    },
    get total() {
      return status.total;
    },
    get processed() {
      return status.processed;
    },
    get stats() {
      return status.stats;
    },
    get action() {
      return status.action;
    },
    get error() {
      return status.error;
    },
    get currentUrl() {
      return status.currentUrl;
    },
    get statusCounts() {
      return status.statusCounts;
    },
    get storeError() {
      return storeError;
    },

    get isProcessing() {
      return status.state === 'processing';
    },
    get isPaused() {
      return status.state === 'paused';
    },
    get isIdle() {
      return status.state === 'idle';
    },
    get progress() {
      if (status.total === 0) return 0;
      return (status.processed / status.total) * 100;
    },

    async load() {
      try {
        const response = await api.getProcessStatus();
        status = {
          state: response.state,
          total: response.total,
          processed: response.processed,
          stats: response.stats,
          action: response.action,
          error: response.error,
          currentUrl: (response as unknown as { current_url?: string }).current_url ?? null,
          statusCounts: (response as unknown as { status_counts?: StatusCounts }).status_counts ?? { ...defaultStatusCounts },
        };
        storeError = null;
      } catch (e) {
        storeError = String(e);
      }
    },

    async start(urls?: string[], screenshots = false) {
      try {
        const response = await api.startProcessing({ urls, screenshots });
        if (response.success) {
          await this.load();
        }
        return response.success;
      } catch (e) {
        storeError = String(e);
        return false;
      }
    },

    async pause() {
      try {
        const response = await api.pauseProcessing();
        if (response.success) {
          await this.load();
        }
        return response.success;
      } catch (e) {
        storeError = String(e);
        return false;
      }
    },

    async resume() {
      try {
        const response = await api.resumeProcessing();
        if (response.success) {
          await this.load();
        }
        return response.success;
      } catch (e) {
        storeError = String(e);
        return false;
      }
    },

    async cancel() {
      try {
        const response = await api.cancelProcessing();
        if (response.success) {
          await this.load();
        }
        return response.success;
      } catch (e) {
        storeError = String(e);
        return false;
      }
    },

    updateStatusCounts(counts: StatusCounts) {
      status.statusCounts = counts;
    },

    setCurrentUrl(url: string | null) {
      status.currentUrl = url;
    },

    clearError() {
      storeError = null;
    },
  };
}

export const processingStore = createProcessingStore();

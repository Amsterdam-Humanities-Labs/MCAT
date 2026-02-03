import { type ProcessingState, IDLE_STATES, ACTIVE_STATES, PAUSED_STATES } from '../../types';
import type { StatusCounts } from '../../types/results';
import { api } from '../api/client';

interface ProcessingStatus {
  state: ProcessingState;
  total: number;
  processed: number;
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
      return ACTIVE_STATES.includes(status.state);
    },
    get isPaused() {
      return PAUSED_STATES.includes(status.state);
    },
    get isIdle() {
      return IDLE_STATES.includes(status.state);
    },
    get progress() {
      if (status.total === 0) return 0;
      return (status.processed / status.total) * 100;
    },

    async start(urls?: string[], screenshots = false) {
      try {
        const response = await api.startProcessing({ urls, screenshots });
        return response.success;
      } catch (e) {
        storeError = String(e);
        return false;
      }
    },

    async pause() {
      try {
        const response = await api.pauseProcessing();
        return response.success;
      } catch (e) {
        storeError = String(e);
        return false;
      }
    },

    async resume() {
      try {
        const response = await api.resumeProcessing();
        return response.success;
      } catch (e) {
        storeError = String(e);
        return false;
      }
    },

    async cancel() {
      try {
        const response = await api.cancelProcessing();
        return response.success;
      } catch (e) {
        storeError = String(e);
        return false;
      }
    },

    clearError() {
      storeError = null;
    },

    updateFromSSE(data: {
      state?: string;
      total?: number;
      processed?: number;
      statusCounts?: StatusCounts;
      action?: string;
      error?: string | null;
      currentUrl?: string | null;
    }) {
      if (data.state !== undefined) status.state = data.state as ProcessingState;
      if (data.total !== undefined) status.total = data.total;
      if (data.processed !== undefined) status.processed = data.processed;
      if (data.action !== undefined) status.action = data.action;
      if (data.error !== undefined) status.error = data.error;
      if (data.currentUrl !== undefined) status.currentUrl = data.currentUrl;
      if (data.statusCounts) {
        status.statusCounts = data.statusCounts;
      }
    },
  };
}

export const processingStore = createProcessingStore();

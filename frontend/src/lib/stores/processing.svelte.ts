import { type ProcessingState, IDLE_STATES, ACTIVE_STATES, PAUSED_STATES } from '../../types';
import type { RunStatusSummary } from '../../types/project';
import { api } from '../api/client';

interface ProcessingStatus {
  state: ProcessingState;
  total: number;
  processed: number;
  action: string;
  error: string | null;
  current_url: string | null;
  status_counts: RunStatusSummary;
}

const defaultStatusCounts: RunStatusSummary = {
  live: 0,
  removed: 0,
  restricted: 0,
  error: 0,
  unknown: 0,
  login_required: 0,
};

function createProcessingStore() {
  let status = $state<ProcessingStatus>({
    state: 'idle',
    total: 0,
    processed: 0,
    action: '',
    error: null,
    current_url: null,
    status_counts: { ...defaultStatusCounts },
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
    get current_url() {
      return status.current_url;
    },
    get statusCounts() {
      return status.status_counts;
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

    clearError() {
      storeError = null;
    },

    reset() {
      status.state = 'idle';
      status.total = 0;
      status.processed = 0;
      status.action = '';
      status.error = null;
      status.current_url = null;
      status.status_counts = { ...defaultStatusCounts };
      storeError = null;
    },

    updateFromSSE(data: {
      state?: string;
      total?: number;
      processed?: number;
      status_counts?: RunStatusSummary;
      action?: string;
      error?: string | null;
      current_url?: string | null;
    }) {
      if (data.state !== undefined) {
        status.state = data.state as ProcessingState;
        if (IDLE_STATES.includes(status.state)) {
          status.total = 0;
          status.processed = 0;
          status.action = '';
          status.error = null;
          status.current_url = null;
          status.status_counts = { ...defaultStatusCounts };
          return;
        }
      }
      if (data.total !== undefined) status.total = data.total;
      if (data.processed !== undefined) status.processed = data.processed;
      if (data.action !== undefined) status.action = data.action;
      if (data.error !== undefined) status.error = data.error;
      if (data.current_url !== undefined) status.current_url = data.current_url;
      if (data.status_counts) {
        status.status_counts = data.status_counts;
      }
    },
  };
}

export const processingStore = createProcessingStore();

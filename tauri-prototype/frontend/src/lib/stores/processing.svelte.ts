import { type ProcessingState, IDLE_STATES, ACTIVE_STATES, PAUSED_STATES } from '../../types';
import type { StatusCounts } from '../../types/results';
import { api } from '../api/client';
import { consoleStore, type LogLevel } from './console.svelte';

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

    async load() {
      try {
        const response = await api.getProcessStatus();
        const newStatusCounts = (response as unknown as { statusCounts?: StatusCounts }).statusCounts;
        const logs = (response as unknown as { logs?: Array<{ id: number; text: string; level: string; timestamp: string }> }).logs;
        const newCurrentUrl = (response as unknown as { currentUrl?: string }).currentUrl ?? null;

        // Only update properties that changed to avoid unnecessary re-renders
        if (status.state !== response.state) status.state = response.state;
        if (status.total !== response.total) status.total = response.total;
        if (status.processed !== response.processed) status.processed = response.processed;
        if (status.action !== response.action) status.action = response.action;
        if (status.error !== response.error) status.error = response.error;
        if (status.currentUrl !== newCurrentUrl) status.currentUrl = newCurrentUrl;

        // Update status counts only if changed
        if (newStatusCounts) {
          const sc = status.statusCounts;
          if (sc.live !== newStatusCounts.live) sc.live = newStatusCounts.live;
          if (sc.removed !== newStatusCounts.removed) sc.removed = newStatusCounts.removed;
          if (sc.restricted !== newStatusCounts.restricted) sc.restricted = newStatusCounts.restricted;
          if (sc.error !== newStatusCounts.error) sc.error = newStatusCounts.error;
          if (sc.pending !== newStatusCounts.pending) sc.pending = newStatusCounts.pending;
        }

        // Add backend logs to console
        if (logs && logs.length > 0) {
          consoleStore.addBackendLogs(logs as Array<{ id: number; text: string; level: LogLevel; timestamp: string }>);
        }

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
      const sc = status.statusCounts;
      if (sc.live !== counts.live) sc.live = counts.live;
      if (sc.removed !== counts.removed) sc.removed = counts.removed;
      if (sc.restricted !== counts.restricted) sc.restricted = counts.restricted;
      if (sc.error !== counts.error) sc.error = counts.error;
      if (sc.pending !== counts.pending) sc.pending = counts.pending;
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

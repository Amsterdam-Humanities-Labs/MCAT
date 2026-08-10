import { getAuthToken } from './client';
import { processingStore } from '../stores/processing.svelte';
import { projectStore } from '../stores/project.svelte';
import { consoleStore } from '../stores/console.svelte';

let consecutiveErrors = 0;

let eventSource: EventSource | null = null;
let reconnectTimeout: ReturnType<typeof setTimeout> | null = null;
let baseUrl = '';

export function initSSE(backendUrl: string) {
  baseUrl = backendUrl;
  connect();
}

export function closeSSE() {
  if (reconnectTimeout) {
    clearTimeout(reconnectTimeout);
    reconnectTimeout = null;
  }
  if (eventSource) {
    eventSource.close();
    eventSource = null;
  }
}

function connect() {
  if (eventSource) {
    eventSource.close();
  }

  // EventSource cannot set headers, so the token travels in the query string.
  eventSource = new EventSource(`${baseUrl}/events?token=${encodeURIComponent(getAuthToken())}`);

  eventSource.onopen = () => {
    if (consecutiveErrors > 0) {
      consoleStore.success('Backend connection restored');
    }
    consecutiveErrors = 0;
    console.log('[SSE] Connected');
  };

  eventSource.onerror = () => {
    consecutiveErrors++;
    eventSource?.close();
    eventSource = null;

    if (consecutiveErrors === 1) {
      consoleStore.warning('Lost connection to backend, reconnecting...');
    } else if (consecutiveErrors % 5 === 0) {
      consoleStore.error(`Backend unreachable (${consecutiveErrors} failed attempts)`);
    }

    if (!reconnectTimeout) {
      reconnectTimeout = setTimeout(() => {
        reconnectTimeout = null;
        connect();
      }, 3000);
    }
  };

  eventSource.addEventListener('project', (event) => {
    try {
      const data = JSON.parse(event.data);
      if (data.project) {
        projectStore.setProject(data.project);
      }
    } catch (e) {
      console.error('[SSE] Failed to parse project event:', e);
    }
  });

  eventSource.addEventListener('processing', (event) => {
    try {
      processingStore.updateFromSSE(JSON.parse(event.data));
    } catch (e) {
      console.error('[SSE] Failed to parse processing event:', e);
    }
  });

  eventSource.addEventListener('log', (event) => {
    try {
      const data = JSON.parse(event.data);
      if (data.log) {
        consoleStore.addBackendLog(data.log);
      }
    } catch (e) {
      console.error('[SSE] Failed to parse log event:', e);
    }
  });
}

export function isConnected(): boolean {
  return eventSource?.readyState === EventSource.OPEN;
}

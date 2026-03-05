import { processingStore } from '../stores/processing.svelte';
import { projectStore } from '../stores/project.svelte';
import { consoleStore } from '../stores/console.svelte';
import { appStore } from '../stores/app.svelte';

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

  eventSource = new EventSource(`${baseUrl}/events`);

  eventSource.onopen = () => {
    console.log('[SSE] Connected');
  };

  eventSource.onerror = () => {
    console.log('[SSE] Connection error, reconnecting...');
    eventSource?.close();
    eventSource = null;

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
      projectStore.setProject(data.project);
      if (data.project) {
        appStore.setView('project');
      } else if (appStore.view === 'project') {
        appStore.setView('start');
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

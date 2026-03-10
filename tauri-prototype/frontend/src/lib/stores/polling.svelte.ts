import { api } from '../api/client';
import { initSSE, closeSSE } from '../api/sse';
import { appStore } from './app.svelte';
import { consoleStore } from './console.svelte';
import { dialogsStore } from './dialogs.svelte';

const HEALTH_CHECK_INTERVAL = 10000;

function createPollingController() {
  let interval: ReturnType<typeof setInterval> | undefined;
  let sseInitialized = false;
  let wasConnected = false;

  async function healthCheck() {
    try {
      await appStore.checkBackendHealth();

      if (appStore.backendConnected && !sseInitialized) {
        const port = await api.getPort();
        initSSE(`http://127.0.0.1:${port}`);
        sseInitialized = true;
      }

      if (appStore.backendConnected && !wasConnected) {
        consoleStore.success('Backend connected');
      } else if (!appStore.backendConnected && wasConnected) {
        consoleStore.error('Backend health check failed — backend may have crashed');
      }
      wasConnected = appStore.backendConnected;

      if (appStore.globalError?.includes('Request failed')) {
        appStore.clearError();
      }
    } catch (e) {
      if (wasConnected) {
        consoleStore.error(`Backend health check error: ${e}`);
        wasConnected = false;
      }
      if (appStore.backendConnected) {
        appStore.setGlobalError(String(e));
      }
    }
  }

  return {
    async checkForInterruptedRun() {
      try {
        const interrupted = await api.getInterruptedRun();
        if (interrupted.has_interrupted && interrupted.run) {
          dialogsStore.showInterruptedRun(interrupted.run);
          return true;
        }
      } catch {
        // No interrupted run
      }
      return false;
    },

    start() {
      healthCheck();
      interval = setInterval(healthCheck, HEALTH_CHECK_INTERVAL);
    },

    stop() {
      if (interval) {
        clearInterval(interval);
        interval = undefined;
      }
      closeSSE();
      sseInitialized = false;
    },
  };
}

export const pollingController = createPollingController();

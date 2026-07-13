import { getBackendUrl } from '../api/client';
import { initSSE, closeSSE } from '../api/sse';
import { appStore } from './app.svelte';
import { consoleStore } from './console.svelte';
const HEALTH_CHECK_INTERVAL = 10000;

function createPollingController() {
  let interval: ReturnType<typeof setInterval> | undefined;
  let sseInitialized = false;
  let wasConnected = false;

  async function healthCheck() {
    try {
      await appStore.checkBackendHealth();

      if (appStore.backendConnected && !sseInitialized) {
        initSSE(getBackendUrl());
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

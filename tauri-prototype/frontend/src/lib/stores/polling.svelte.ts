import { api } from '../api/client';
import { appStore } from './app.svelte';
import { projectStore } from './project.svelte';
import { processingStore } from './processing.svelte';
import { resultsStore } from './results.svelte';
import { dialogsStore } from './dialogs.svelte';

const POLL_INTERVAL = 2000;

function createPollingController() {
  let interval: ReturnType<typeof setInterval> | undefined;
  let lastLogId = $state(-1);

  async function refresh() {
    try {
      await appStore.checkBackendHealth();

      const projStatus = await api.getProject();
      projectStore.setProject(projStatus.project);

      if (projStatus.project) {
        await processingStore.load();
        if (appStore.view !== 'wizard') {
          appStore.setView('project');
        }

        // Load results and update status counts when idle
        const statusCounts = await resultsStore.load();
        if (statusCounts && processingStore.isIdle) {
          processingStore.updateStatusCounts(statusCounts);
        }
      } else if (appStore.view === 'project') {
        appStore.setView('start');
      }

      // Clear stale connection errors
      if (appStore.globalError?.includes('Request failed')) {
        appStore.clearError();
      }
    } catch (e) {
      if (appStore.backendConnected) {
        appStore.setGlobalError(String(e));
      }
    }
  }

  return {
    get lastLogId() {
      return lastLogId;
    },

    async checkForInterruptedRun() {
      try {
        const interrupted = await api.getInterruptedRun();
        if (interrupted.hasInterrupted && interrupted.run) {
          dialogsStore.showInterruptedRun(interrupted.run);
          return true;
        }
      } catch {
        // No interrupted run
      }
      return false;
    },

    start() {
      refresh();
      interval = setInterval(refresh, POLL_INTERVAL);
    },

    stop() {
      if (interval) {
        clearInterval(interval);
        interval = undefined;
      }
    },

    async refreshNow() {
      await refresh();
    },
  };
}

export const pollingController = createPollingController();

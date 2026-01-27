import { api } from '../api/client';

export type ViewState = 'start' | 'wizard' | 'project';

interface AppState {
  view: ViewState;
  backendConnected: boolean;
  globalError: string | null;
}

function createAppStore() {
  let state = $state<AppState>({
    view: 'start',
    backendConnected: false,
    globalError: null,
  });

  return {
    get view() {
      return state.view;
    },
    get backendConnected() {
      return state.backendConnected;
    },
    get globalError() {
      return state.globalError;
    },

    setView(view: ViewState) {
      state.view = view;
    },

    setBackendConnected(connected: boolean) {
      state.backendConnected = connected;
    },

    setGlobalError(error: string | null) {
      state.globalError = error;
    },

    clearError() {
      state.globalError = null;
    },

    async checkBackendHealth() {
      try {
        const response = await api.health();
        state.backendConnected = response.status === 'ok';
        return state.backendConnected;
      } catch {
        state.backendConnected = false;
        return false;
      }
    },
  };
}

export const appStore = createAppStore();

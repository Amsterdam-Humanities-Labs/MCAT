import type { Platform } from '../../types';
import { api } from '../api/client';

export interface WizardState {
  name: string;
  platform: Platform;
  location: string;
  csv_path: string;
  columns: string[];
  url_column: string;
  error: string | null;
  loading: boolean;
}

function createWizardStore() {
  const defaultState: WizardState = {
    name: '',
    platform: 'youtube',
    location: '',
    csv_path: '',
    columns: [],
    url_column: '',
    error: null,
    loading: false,
  };

  let state = $state<WizardState>({ ...defaultState });

  return {
    get name() {
      return state.name;
    },
    get platform() {
      return state.platform;
    },
    get location() {
      return state.location;
    },
    get csv_path() {
      return state.csv_path;
    },
    get columns() {
      return state.columns;
    },
    get url_column() {
      return state.url_column;
    },
    get error() {
      return state.error;
    },
    get loading() {
      return state.loading;
    },

    setName(name: string) {
      state.name = name;
    },

    setPlatform(platform: Platform) {
      state.platform = platform;
    },

    setLocation(location: string) {
      state.location = location;
    },

    setCsvPath(path: string) {
      state.csv_path = path;
    },

    setUrlColumn(column: string) {
      state.url_column = column;
    },

    setError(error: string | null) {
      state.error = error;
    },

    async loadCsvColumns(path: string) {
      state.loading = true;
      state.error = null;

      try {
        const info = await api.loadCsv(path);
        state.columns = info.columns;
        state.csv_path = path;

        // Auto-detect URL column
        const detection = await api.detectUrlColumn(info.columns);
        if (detection.recommended) {
          state.url_column = detection.recommended;
        } else if (detection.candidates.length > 0) {
          state.url_column = detection.candidates[0];
        }
      } catch (e) {
        state.error = `Failed to load CSV: ${e}`;
      } finally {
        state.loading = false;
      }
    },

    canCreate() {
      return (
        state.name.trim() !== '' &&
        state.platform !== null &&
        state.location.trim() !== '' &&
        state.csv_path.trim() !== '' &&
        state.url_column.trim() !== ''
      );
    },

    reset() {
      Object.assign(state, defaultState);
    },

    getCreateData() {
      return {
        name: state.name,
        platform: state.platform,
        location: state.location,
        csv_path: state.csv_path,
        url_column: state.url_column,
      };
    },
  };
}

export const wizardStore = createWizardStore();

import type { Platform } from '../../types';
import { api } from '../api/client';

export interface WizardState {
  step: 1 | 2;
  name: string;
  platform: Platform;
  location: string;
  csv_path: string;
  columns: string[];
  url_column: string;
  preserve_columns: string[];
  error: string | null;
  loading: boolean;
}

function createWizardStore() {
  const defaultState: WizardState = {
    step: 1,
    name: '',
    platform: 'youtube',
    location: '',
    csv_path: '',
    columns: [],
    url_column: '',
    preserve_columns: [],
    error: null,
    loading: false,
  };

  let state = $state<WizardState>({ ...defaultState });

  return {
    get step() {
      return state.step;
    },
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
    get preserve_columns() {
      return state.preserve_columns;
    },
    get error() {
      return state.error;
    },
    get loading() {
      return state.loading;
    },

    setStep(step: 1 | 2) {
      state.step = step;
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

    setPreserveColumns(columns: string[]) {
      state.preserve_columns = columns;
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

    canProceedToStep2() {
      return (
        state.name.trim() !== '' &&
        state.platform !== null &&
        state.location.trim() !== '' &&
        state.csv_path.trim() !== ''
      );
    },

    canCreate() {
      return (
        this.canProceedToStep2() &&
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
        preserve_columns: state.preserve_columns,
      };
    },
  };
}

export const wizardStore = createWizardStore();

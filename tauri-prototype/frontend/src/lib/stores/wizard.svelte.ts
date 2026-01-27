import type { Platform } from '../../types';
import { api } from '../api/client';

export interface WizardState {
  step: 1 | 2;
  name: string;
  platform: Platform;
  location: string;
  csvPath: string;
  columns: string[];
  urlColumn: string;
  preserveColumns: string[];
  error: string | null;
  loading: boolean;
}

function createWizardStore() {
  const defaultState: WizardState = {
    step: 1,
    name: '',
    platform: 'youtube',
    location: '',
    csvPath: '',
    columns: [],
    urlColumn: '',
    preserveColumns: [],
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
    get csvPath() {
      return state.csvPath;
    },
    get columns() {
      return state.columns;
    },
    get urlColumn() {
      return state.urlColumn;
    },
    get preserveColumns() {
      return state.preserveColumns;
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

    setCsvPath(csvPath: string) {
      state.csvPath = csvPath;
    },

    setUrlColumn(column: string) {
      state.urlColumn = column;
    },

    setPreserveColumns(columns: string[]) {
      state.preserveColumns = columns;
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
        state.csvPath = path;

        // Auto-detect URL column
        const detection = await api.detectUrlColumn(info.columns);
        if (detection.recommended) {
          state.urlColumn = detection.recommended;
        } else if (detection.candidates.length > 0) {
          state.urlColumn = detection.candidates[0];
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
        state.csvPath.trim() !== ''
      );
    },

    canCreate() {
      return (
        this.canProceedToStep2() &&
        state.urlColumn.trim() !== ''
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
        csvPath: state.csvPath,
        urlColumn: state.urlColumn,
        preserveColumns: state.preserveColumns,
      };
    },
  };
}

export const wizardStore = createWizardStore();

import { api } from '../api/client';
import type { ResultRow, StatusCounts } from '../../types/results';

function createResultsStore() {
  let results = $state<ResultRow[]>([]);
  let loading = $state(false);

  return {
    get results() {
      return results;
    },
    get loading() {
      return loading;
    },
    get count() {
      return results.length;
    },

    async load(): Promise<StatusCounts | null> {
      loading = true;
      try {
        const combined = await api.getCombinedResults();
        results = combined.results;
        return combined.byStatus;
      } catch {
        return null;
      } finally {
        loading = false;
      }
    },

    clear() {
      results = [];
    },
  };
}

export const resultsStore = createResultsStore();

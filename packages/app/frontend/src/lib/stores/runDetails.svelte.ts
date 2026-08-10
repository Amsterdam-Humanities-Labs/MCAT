import { api } from '../api/client';

interface Entry {
  columns: string[];
  rows: Record<string, unknown>[];
  loading: boolean;
  error: string | null;
}

type Fetcher = () => Promise<{ columns: string[]; rows: Record<string, unknown>[] }>;

/**
 * Cached run results and changes, keyed by project path plus run id.
 *
 * The timeline only shows completed and abandoned runs, whose results.csv and
 * changes.csv are written once and never touched again, so entries never go
 * stale and need no invalidation. Caching also survives the detail panel being
 * unmounted, which happens every time a run row is collapsed.
 *
 * Run ids are second-resolution timestamps and can repeat across projects, so
 * the key includes the project path; a leftover entry from another project can
 * then never be hit, which makes reset() cleanup rather than correctness.
 */
function createRunDetailsStore() {
  const changes = $state<Record<string, Entry>>({});
  const results = $state<Record<string, Entry>>({});

  const keyOf = (projectPath: string, runId: string) => `${projectPath}::${runId}`;

  async function load(bucket: Record<string, Entry>, key: string, fetcher: Fetcher) {
    // A settled success is final. A previous failure is retried.
    const existing = bucket[key];
    if (existing && (existing.loading || existing.error === null)) return;

    bucket[key] = { columns: [], rows: [], loading: true, error: null };
    try {
      const res = await fetcher();
      bucket[key] = { columns: res.columns, rows: res.rows, loading: false, error: null };
    } catch (e) {
      bucket[key] = {
        columns: [],
        rows: [],
        loading: false,
        error: e instanceof Error ? e.message : String(e),
      };
    }
  }

  return {
    changes(projectPath: string, runId: string): Entry | null {
      return changes[keyOf(projectPath, runId)] ?? null;
    },

    results(projectPath: string, runId: string): Entry | null {
      return results[keyOf(projectPath, runId)] ?? null;
    },

    loadChanges(projectPath: string, runId: string) {
      return load(changes, keyOf(projectPath, runId), () => api.getRunChangedResults(runId));
    },

    loadResults(projectPath: string, runId: string) {
      return load(results, keyOf(projectPath, runId), () => api.getRunResults(runId));
    },

    reset() {
      for (const k of Object.keys(changes)) delete changes[k];
      for (const k of Object.keys(results)) delete results[k];
    },
  };
}

export const runDetailsStore = createRunDetailsStore();

import type { Project, CreateProjectRequest } from '../../types';
import { api } from '../api/client';

function createProjectStore() {
  let project = $state<Project | null>(null);
  let error = $state<string | null>(null);
  let loading = $state(false);

  const sortedRuns = $derived.by(() => {
    if (!project?.runs) return [];
    return [...project.runs]
      .filter((r) => r.status === 'completed')
      .sort((a, b) => new Date(a.started_at).getTime() - new Date(b.started_at).getTime());
  });

  const latestRun = $derived.by(() => {
    const runs = sortedRuns;
    return runs.length > 0 ? runs[runs.length - 1] : null;
  });

  const baselineRun = $derived.by(() => {
    return sortedRuns.find((r) => r.is_baseline) ?? null;
  });

  return {
    get project() {
      return project;
    },
    get error() {
      return error;
    },
    get loading() {
      return loading;
    },
    get hasProject() {
      return project !== null;
    },
    get sortedRuns() {
      return sortedRuns;
    },
    get latestRun() {
      return latestRun;
    },
    get baselineRun() {
      return baselineRun;
    },

    async create(data: CreateProjectRequest) {
      loading = true;
      error = null;
      try {
        const response = await api.createProject(data);
        if (response.project) {
          project = response.project;
        }
        return response.success;
      } catch (e) {
        error = e instanceof Error ? e.message : String(e);
        return false;
      } finally {
        loading = false;
      }
    },

    async open(path: string) {
      loading = true;
      error = null;
      try {
        const response = await api.openProject(path);
        if (response.project) {
          project = response.project;
        }
        return response.success;
      } catch (e) {
        error = e instanceof Error ? e.message : String(e);
        return false;
      } finally {
        loading = false;
      }
    },

    async close() {
      loading = true;
      error = null;
      try {
        await api.closeProject();
        project = null;
      } catch (e) {
        error = e instanceof Error ? e.message : String(e);
      } finally {
        loading = false;
      }
    },

    setProject(p: Project | null) {
      project = p;
    },

    clearError() {
      error = null;
    },
  };
}

export const projectStore = createProjectStore();

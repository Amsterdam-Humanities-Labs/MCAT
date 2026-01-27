import type { Project, CreateProjectRequest } from '../../types';
import { api } from '../api/client';

function createProjectStore() {
  let project = $state<Project | null>(null);
  let error = $state<string | null>(null);
  let loading = $state(false);

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

    async load() {
      loading = true;
      error = null;
      try {
        const response = await api.getProject();
        project = response.project;
      } catch (e) {
        error = String(e);
      } finally {
        loading = false;
      }
    },

    async create(data: CreateProjectRequest) {
      loading = true;
      error = null;
      try {
        const response = await api.createProject(data);
        if (response.success) {
          await this.load();
          return true;
        }
        return false;
      } catch (e) {
        error = String(e);
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
        if (response.success) {
          await this.load();
          return true;
        }
        return false;
      } catch (e) {
        error = String(e);
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
        error = String(e);
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

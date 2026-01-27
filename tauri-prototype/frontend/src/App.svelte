<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { open } from '@tauri-apps/plugin-dialog';
  import { api } from '$lib/api/client';
  import { cn } from '$lib/utils';
  import { appStore } from '$lib/stores/app.svelte';
  import { wizardStore } from '$lib/stores/wizard.svelte';
  import { processingStore } from '$lib/stores/processing.svelte';
  import { consoleStore } from '$lib/stores/console.svelte';
  import ErrorBanner from '$lib/components/display/ErrorBanner.svelte';
  import StartScreen from '$lib/views/StartScreen.svelte';
  import ProjectWizard from '$lib/views/ProjectWizard.svelte';
  import ProjectView from '$lib/views/ProjectView.svelte';
  import InterruptedRunDialog from '$lib/views/dialogs/InterruptedRunDialog.svelte';
  import AddUrlsDialog from '$lib/views/dialogs/AddUrlsDialog.svelte';
  import ExportDialog from '$lib/views/dialogs/ExportDialog.svelte';
  import type { Project } from '$types/project';
  import type { ResultRow } from '$types/results';

  interface Props {
    class?: string;
  }

  let { class: className }: Props = $props();

  // State
  let project = $state<Project | null>(null);
  let results = $state<ResultRow[]>([]);
  let pollInterval: ReturnType<typeof setInterval> | undefined;

  // Dialog states
  let showInterruptedRunDialog = $state(false);
  let interruptedRun = $state<{ runId: string; processed: number; total: number; remaining: number } | null>(null);
  let showAddUrlsDialog = $state(false);
  let showExportDialog = $state(false);

  async function refreshStatus() {
    try {
      await appStore.checkBackendHealth();

      const projStatus = await api.getProject();
      project = projStatus.project;

      if (project) {
        await processingStore.load();
        appStore.setView('project');

        // Load results
        try {
          const combined = await api.getCombinedResults();
          results = combined.results;
          processingStore.updateStatusCounts(combined.byStatus);
        } catch {
          // Results may not be available yet
        }
      } else if (appStore.view === 'project') {
        appStore.setView('start');
      }

      // Clear connection errors
      if (appStore.globalError?.includes('Request failed')) {
        appStore.clearError();
      }
    } catch (e) {
      if (appStore.backendConnected) {
        appStore.setGlobalError(String(e));
      }
    }
  }

  async function handleNewProject() {
    wizardStore.reset();
    appStore.setView('wizard');
  }

  async function handleOpenProject() {
    try {
      const selected = await open({
        multiple: false,
        filters: [{ name: 'Project', extensions: ['json'] }],
        title: 'Open MCAT Project',
      });

      if (!selected) return;

      const result = await api.openProject(selected as string);
      if (result?.success) {
        await refreshStatus();

        // Check for interrupted run
        try {
          const interrupted = await api.getInterruptedRun();
          if (interrupted.hasInterrupted && interrupted.run) {
            interruptedRun = interrupted.run;
            showInterruptedRunDialog = true;
          }
        } catch {
          // Ignore - no interrupted run
        }
      }
    } catch (e) {
      appStore.setGlobalError(String(e));
    }
  }

  async function handleWizardComplete(data: ReturnType<typeof wizardStore.getCreateData>) {
    try {
      const result = await api.createProject({
        name: data.name,
        platform: data.platform,
        location: data.location,
        csvPath: data.csvPath,
        urlColumn: data.urlColumn,
      });

      if (result?.success) {
        consoleStore.success('Project created successfully');
        await refreshStatus();
      }
    } catch (e) {
      appStore.setGlobalError(String(e));
    }
  }

  function handleWizardCancel() {
    wizardStore.reset();
    appStore.setView('start');
  }

  async function handleCloseProject() {
    try {
      await api.closeProject();
      project = null;
      results = [];
      appStore.setView('start');
    } catch (e) {
      appStore.setGlobalError(String(e));
    }
  }

  async function handleResumeRun() {
    if (!interruptedRun) return;
    try {
      await api.resumeRun(interruptedRun.runId);
      consoleStore.info(`Resuming run ${interruptedRun.runId}`);
      showInterruptedRunDialog = false;
      interruptedRun = null;
      await refreshStatus();
    } catch (e) {
      appStore.setGlobalError(String(e));
    }
  }

  async function handleAbandonRun() {
    if (!interruptedRun) return;
    try {
      await api.abandonRun(interruptedRun.runId);
      consoleStore.warning(`Abandoned run ${interruptedRun.runId}`);
      showInterruptedRunDialog = false;
      interruptedRun = null;
    } catch (e) {
      appStore.setGlobalError(String(e));
    }
  }

  async function handleImportUrls(_csvPath: string) {
    try {
      const result = await api.confirmImport();
      consoleStore.success(`Added ${result.added} new URLs`);
      showAddUrlsDialog = false;
      await refreshStatus();
    } catch (e) {
      appStore.setGlobalError(String(e));
    }
  }

  onMount(async () => {
    await refreshStatus();
    pollInterval = setInterval(refreshStatus, 2000);
  });

  onDestroy(() => {
    if (pollInterval) clearInterval(pollInterval);
  });
</script>

<main class={cn('max-w-4xl mx-auto p-4 min-h-screen bg-mcat-bg text-mcat-text font-sans', className)}>
  <!-- Header -->
  <header class="flex items-baseline gap-4 mb-6 pb-4 border-b border-mcat-border">
    <h1 class="m-0 text-mcat-orange text-2xl font-bold">MCAT</h1>
    <span class="text-mcat-text-muted text-sm">Moderation Content Analysis Tool</span>
    <span
      class={cn(
        'ml-auto px-3 py-1 rounded text-sm',
        appStore.backendConnected
          ? 'bg-mcat-success-bg text-mcat-success'
          : 'bg-mcat-border text-mcat-text-muted'
      )}
    >
      Backend: {appStore.backendConnected ? 'Connected' : 'Connecting...'}
    </span>
  </header>

  <!-- Error banner -->
  {#if appStore.globalError}
    <ErrorBanner
      message={appStore.globalError}
      class="mb-4"
      ondismiss={() => appStore.clearError()}
    />
  {/if}

  <!-- Views -->
  {#if appStore.view === 'start'}
    <StartScreen
      onnewproject={handleNewProject}
      onopenproject={handleOpenProject}
    />
  {:else if appStore.view === 'wizard'}
    <ProjectWizard
      oncancel={handleWizardCancel}
      oncomplete={handleWizardComplete}
    />
  {:else if appStore.view === 'project' && project}
    <ProjectView
      {project}
      {results}
      onclose={handleCloseProject}
      onaddurls={() => (showAddUrlsDialog = true)}
      onexport={() => (showExportDialog = true)}
    />
  {/if}

  <!-- Dialogs -->
  <InterruptedRunDialog
    open={showInterruptedRunDialog}
    run={interruptedRun}
    onresume={handleResumeRun}
    onabandon={handleAbandonRun}
    onclose={() => (showInterruptedRunDialog = false)}
  />

  <AddUrlsDialog
    open={showAddUrlsDialog}
    onclose={() => (showAddUrlsDialog = false)}
    onimport={handleImportUrls}
  />

  <ExportDialog
    open={showExportDialog}
    onclose={() => (showExportDialog = false)}
  />
</main>

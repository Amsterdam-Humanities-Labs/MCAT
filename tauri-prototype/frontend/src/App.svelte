<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { open } from '@tauri-apps/plugin-dialog';
  import { api } from '$lib/api/client';
  import { cn } from '$lib/utils';
  import { appStore } from '$lib/stores/app.svelte';
  import { projectStore } from '$lib/stores/project.svelte';
  import { wizardStore } from '$lib/stores/wizard.svelte';
  import { resultsStore } from '$lib/stores/results.svelte';
  import { dialogsStore } from '$lib/stores/dialogs.svelte';
  import { consoleStore } from '$lib/stores/console.svelte';
  import { processingStore } from '$lib/stores/processing.svelte';
  import { pollingController } from '$lib/stores/polling.svelte';
  import { ErrorBanner } from '$lib/components';
  import StartScreen from '$lib/views/StartScreen.svelte';
  import ProjectWizard from '$lib/views/ProjectWizard.svelte';
  import ProjectView from '$lib/views/ProjectView.svelte';
  import InterruptedRunDialog from '$lib/views/dialogs/InterruptedRunDialog.svelte';
  import AddUrlsDialog from '$lib/views/dialogs/AddUrlsDialog.svelte';

  interface Props {
    class?: string;
  }

  let { class: className }: Props = $props();

  // Handlers
  function handleNewProject() {
    wizardStore.reset();
    appStore.setView('wizard');
  }

  async function handleOpenProject() {
    const selected = await open({
      multiple: false,
      filters: [{ name: 'Project', extensions: ['json'] }],
      title: 'Open MCAT Project',
    });
    if (!selected) return;

    try {
      const success = await projectStore.open(selected as string);
      if (success) {
        await pollingController.checkForInterruptedRun();
      }
    } catch (e) {
      appStore.setGlobalError(String(e));
    }
  }

  async function handleWizardComplete(data: ReturnType<typeof wizardStore.getCreateData>) {
    try {
      const success = await projectStore.create({
        name: data.name,
        platform: data.platform,
        location: data.location,
        csvPath: data.csvPath,
        urlColumn: data.urlColumn,
      });
      if (success) {
        consoleStore.success('Project created successfully');
        appStore.setView('project');
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
      await projectStore.close();
      resultsStore.clear();
      appStore.setView('start');
    } catch (e) {
      appStore.setGlobalError(String(e));
    }
  }

  async function handleResumeRun() {
    const run = dialogsStore.interruptedRun;
    if (!run) return;
    try {
      await api.resumeRun(run.runId);
      consoleStore.info(`Resuming run ${run.runId}`);
      dialogsStore.closeInterruptedRun();
    } catch (e) {
      appStore.setGlobalError(String(e));
    }
  }

  async function handleAbandonRun() {
    const run = dialogsStore.interruptedRun;
    if (!run) return;
    try {
      await api.abandonRun(run.runId);
      consoleStore.warning(`Abandoned run ${run.runId}`);
      dialogsStore.closeInterruptedRun();
    } catch (e) {
      appStore.setGlobalError(String(e));
    }
  }

  async function handleImportUrls() {
    try {
      const result = await api.confirmImport();
      consoleStore.success(`Added ${result.added} new URLs`);
      dialogsStore.closeAddUrls();
    } catch (e) {
      appStore.setGlobalError(String(e));
    }
  }

  onMount(() => pollingController.start());
  onDestroy(() => pollingController.stop());
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
      wizard={wizardStore}
      oncancel={handleWizardCancel}
      oncomplete={handleWizardComplete}
    />
  {:else if appStore.view === 'project' && projectStore.project}
    <ProjectView
      project={projectStore.project}
      results={resultsStore.results}
      processing={processingStore}
      messages={consoleStore.messages}
      onclose={handleCloseProject}
      onaddurls={() => dialogsStore.openAddUrls()}
    />
  {/if}

  <!-- Dialogs -->
  <InterruptedRunDialog
    open={dialogsStore.interruptedRunOpen}
    run={dialogsStore.interruptedRun}
    onresume={handleResumeRun}
    onabandon={handleAbandonRun}
    onclose={() => dialogsStore.closeInterruptedRun()}
  />

  <AddUrlsDialog
    open={dialogsStore.addUrlsOpen}
    onclose={() => dialogsStore.closeAddUrls()}
    onimport={handleImportUrls}
  />
</main>

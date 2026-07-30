<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { api } from '$lib/api/client';
  import { cn } from '$lib/utils';
  import { appStore } from '$lib/stores/app.svelte';
  import { projectStore } from '$lib/stores/project.svelte';
  import { wizardStore } from '$lib/stores/wizard.svelte';
  import { dialogsStore } from '$lib/stores/dialogs.svelte';
  import { consoleStore } from '$lib/stores/console.svelte';
  import { processingStore } from '$lib/stores/processing.svelte';
  import { pollingController } from '$lib/stores/polling.svelte';
  import { ErrorBanner } from '$lib/components';
  import StartScreen from '$lib/views/StartScreen.svelte';
  import ProjectWizard from '$lib/views/ProjectWizard.svelte';
  import ProjectView from '$lib/views/ProjectView.svelte';
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
    try {
      const result = await api.pickFile([{ name: 'Project', extensions: ['json'] }]);
      if (!result.path) return;

      processingStore.reset();
      const success = await projectStore.open(result.path);
      if (success) {
        appStore.setView('project');
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
        csv_path: data.csv_path,
        url_column: data.url_column,
      });
      if (success) {
        consoleStore.success('Project created successfully');
        appStore.setView('project');
      } else {
        wizardStore.setError(projectStore.error ?? 'Failed to create project');
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
      processingStore.reset();
      consoleStore.clear();
      appStore.setView('start');
    } catch (e) {
      appStore.setGlobalError(String(e));
    }
  }

  async function handleImportUrls() {
    try {
      const result = await api.confirmImport();
      if (result.project) projectStore.setProject(result.project);
      consoleStore.success(`Added ${result.added} new URLs`);
      dialogsStore.closeAddUrls();
    } catch (e) {
      appStore.setGlobalError(String(e));
    }
  }

  onMount(() => pollingController.start());
  onDestroy(() => pollingController.stop());
</script>

<main class={cn('min-h-screen bg-bg-primary text-text-body', className)}>

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
      processing={processingStore}
      messages={consoleStore.filteredMessages}
      onclose={handleCloseProject}
    />
  {/if}

  <!-- Dialogs -->
  <AddUrlsDialog
    open={dialogsStore.addUrlsOpen}
    onclose={() => dialogsStore.closeAddUrls()}
    onimport={handleImportUrls}
  />
</main>

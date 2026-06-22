<script lang="ts">
  import { Toolbar, Controls, ProgressSection, ConsolePanel, Dialog, Button } from '$lib/components';
  import Timeline from '$lib/components/Timeline.svelte';
  import { projectStore } from '$lib/stores/project.svelte';
  import { api } from '$lib/api/client';
  import type { Project } from '$types/project';
  import type { LogMessage } from '$types/console';
  import type { processingStore as ProcessingStoreType } from '$lib/stores/processing.svelte';

  interface Props {
    project: Project;
    processing: typeof ProcessingStoreType;
    messages: LogMessage[];
    onclose?: () => void;
  }

  let { project, processing, messages, onclose }: Props = $props();

  let selectedRunId = $state<string | null>(null);
  let confirmAbandonOpen = $state(false);
  let intervalEnabled = $derived(project.tracking?.enabled ?? false);
  let intervalValue = $derived(project.tracking?.interval_value ?? 30);
  let intervalUnit = $derived(project.tracking?.interval_unit ?? 'minutes') as 'minutes' | 'hours' | 'days';

  // Derive run state from processing store
  const runState = $derived.by((): 'idle' | 'running' | 'paused' => {
    if (processing.isPaused) return 'paused';
    if (processing.isProcessing) return 'running';
    return 'idle';
  });

  const lastRunDuration = $derived.by(() => {
    const latest = projectStore.latestRun;
    return latest?.duration_seconds ?? null;
  });

  const currentRun = $derived.by(() => {
    if (runState === 'idle') return null;
    return {
      timestamp: new Date().toISOString(),
      paused: runState === 'paused',
    };
  });

  async function handleStart() {
    if (intervalEnabled) {
      try {
        await api.startTracking(intervalValue, intervalUnit);
      } catch (e) {
        console.error('Failed to start tracking:', e);
      }
    }
    processing.start();
  }

  async function handleOpenFolder() {
    try {
      await api.openExternal(project.path);
    } catch {
      // fallback: ignore
    }
  }

  async function handleSetupBrowser() {
    try {
      await api.startLogin();
    } catch (e) {
      console.error('Browser setup failed:', e);
    }
  }

  async function handleResetBrowser() {
    try {
      const r = await api.logout();
      if (r.project) projectStore.setProject(r.project);
    } catch (e) {
      console.error('Reset failed:', e);
    }
  }

  function handleRunClick(id: string) {
    selectedRunId = selectedRunId === id ? null : id;
  }

  async function confirmAbandon() {
    confirmAbandonOpen = false;
    await processing.abandon();
  }
</script>

<div class="flex flex-col h-screen overflow-hidden">
  <Toolbar
    projectName={project.name}
    platform={project.platform}
    urlCount={project.url_count}
    projectPath={project.path}
    auth={project.auth}
    onOpenFolder={handleOpenFolder}
    onClose={onclose}
    onSetupBrowser={handleSetupBrowser}
    onResetBrowser={handleResetBrowser}
  />

  <Controls
    {runState}
    {intervalEnabled}
    {intervalValue}
    {intervalUnit}
    screenshotsEnabled={project.screenshots_enabled ?? false}
    {lastRunDuration}
    nextCheck={project.tracking?.next_check ?? null}
    runNumber={project.runs?.length ?? 0}
    onStart={handleStart}
    onPause={() => processing.pause()}
    onResume={() => processing.resume()}
    onAbandon={() => (confirmAbandonOpen = true)}
    onIntervalToggle={async (v) => { const r = await api.setTrackingConfig({ enabled: v }); if (r.project) projectStore.setProject(r.project); }}
    onIntervalChange={async (v, u) => { const r = await api.setTrackingConfig({ interval_value: v, interval_unit: u }); if (r.project) projectStore.setProject(r.project); }}
    onScreenshotsToggle={async (v) => { const r = await api.setScreenshots(v); if (r.project) projectStore.setProject(r.project); }}
  />

  {#if !processing.isIdle}
    <ProgressSection
      total={processing.total}
      checked={processing.processed}
      statusCounts={processing.statusCounts}
      baselineCounts={projectStore.baselineRun?.status_summary ?? null}
    />
  {/if}

  <Timeline
    runs={project.runs ?? []}
    {currentRun}
    {selectedRunId}
    projectPath={project.path}
    totalUrls={project.url_count}
    onRunClick={handleRunClick}
  />

  <ConsolePanel {messages} />
</div>

<Dialog
  bind:open={confirmAbandonOpen}
  title="Abandon run?"
  onclose={() => (confirmAbandonOpen = false)}
>
  <p class="text-base text-text-body m-0">
    The current run will be stopped and saved as abandoned. Partial results are
    kept, but the run can't be resumed.
  </p>

  {#snippet actions()}
    <Button variant="secondary" onclick={() => (confirmAbandonOpen = false)}>
      Go back
    </Button>
    <Button variant="danger" onclick={confirmAbandon}>
      Abandon run
    </Button>
  {/snippet}
</Dialog>

<script lang="ts">
  import { Toolbar, Controls, ProgressSection, ConsolePanel } from '$lib/components';
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
      progressPercent: processing.progress ? Math.round(processing.progress) : 0,
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

  let loginInProgress = $state(false);

  async function handleOpenFolder() {
    try {
      await api.openExternal(project.path);
    } catch {
      // fallback: ignore
    }
  }

  async function handleLogin() {
    try {
      const result = await api.startLogin();
      if (!result.success) return;
      loginInProgress = true;
    } catch (e) {
      console.error('Login failed:', e);
    }
  }

  async function handleLoginDone() {
    try {
      const complete = await api.completeLogin();
      loginInProgress = false;
      if (complete.success) {
        const r = await api.openProject(project.path);
        if (r.project) projectStore.setProject(r.project);
      }
    } catch (e) {
      console.error('Complete login failed:', e);
    }
  }

  async function handleLoginCancel() {
    try {
      await api.cancelLogin();
    } catch (e) {
      console.error('Cancel login failed:', e);
    }
    loginInProgress = false;
  }

  async function handleLogout() {
    try {
      const r = await api.logout();
      if (r.project) projectStore.setProject(r.project);
    } catch (e) {
      console.error('Logout failed:', e);
    }
  }

  function handleRunClick(id: string) {
    selectedRunId = selectedRunId === id ? null : id;
  }
</script>

<div class="flex flex-col h-screen overflow-hidden">
  <Toolbar
    projectName={project.name}
    platform={project.platform}
    urlCount={project.url_count}
    projectPath={project.path}
    auth={project.auth}
    {loginInProgress}
    onOpenFolder={handleOpenFolder}
    onClose={onclose}
    onLogin={handleLogin}
    onLoginDone={handleLoginDone}
    onLoginCancel={handleLoginCancel}
    onLogout={handleLogout}
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

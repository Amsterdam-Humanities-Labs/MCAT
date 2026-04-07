<script lang="ts">
  import { Toolbar, Controls, ProgressSection, ConsolePanel } from '$lib/components';
  import Timeline from '$lib/components/Timeline.svelte';
  import { projectStore } from '$lib/stores/project.svelte';
  import { api } from '$lib/api/client';
  import type { Project, RunStatusSummary } from '$types/project';
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

  // Status counts from processing (live SSE) or last run
  const statusCounts = $derived.by((): RunStatusSummary => {
    if (processing.statusCounts) {
      return {
        live: processing.statusCounts.live ?? 0,
        removed: processing.statusCounts.removed ?? 0,
        restricted: processing.statusCounts.restricted ?? 0,
        error: processing.statusCounts.error ?? 0,
      };
    }
    return { live: 0, removed: 0, restricted: 0, error: 0 };
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

  async function handleOpenFolder() {
    try {
      await api.openExternal(project.path);
    } catch {
      // fallback: ignore
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
    onOpenFolder={handleOpenFolder}
    onClose={onclose}
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
    onIntervalToggle={(v) => api.setTrackingConfig({ enabled: v })}
    onIntervalChange={(v, u) => api.setTrackingConfig({ interval_value: v, interval_unit: u })}
    onScreenshotsToggle={(v) => api.setScreenshots(v)}
  />

  <ProgressSection
    total={processing.total || project.url_count}
    checked={processing.processed}
    {statusCounts}
    baselineCounts={projectStore.baselineRun?.status_summary ?? null}
  />

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

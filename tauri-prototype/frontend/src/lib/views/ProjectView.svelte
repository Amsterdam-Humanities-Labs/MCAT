<script lang="ts">
  import { cn } from '$lib/utils';
  import {
    Button,
    Badge,
    SegmentedProgress,
    ConsolePanel,
    DataTable,
    TrackingControls,
    TrackingHistory,
  } from '$lib/components';
  import { trackingStore } from '$lib/stores/tracking.svelte';
  import { api } from '$lib/api/client';
  import type { Project } from '$types/project';
  import type { ResultRow } from '$types/results';
  import type { LogMessage } from '$lib/stores/console.svelte';
  import type { processingStore as ProcessingStoreType } from '$lib/stores/processing.svelte';

  interface Props {
    project: Project;
    results?: ResultRow[];
    processing: typeof ProcessingStoreType;
    messages: LogMessage[];
    class?: string;
    onclose?: () => void;
    onaddurls?: () => void;
  }

  let {
    project,
    results = [],
    processing,
    messages,
    class: className,
    onclose,
    onaddurls,
  }: Props = $props();

  let selectedTrackingRunId = $state<string | null>(null);
  let trackingRunResults = $state<ResultRow[]>([]);

  async function handleSelectTrackingRun(runId: string) {
    selectedTrackingRunId = runId;
    try {
      const result = await api.getRunResults(runId);
      trackingRunResults = result.results || [];
    } catch (error) {
      console.error('Failed to load tracking run results:', error);
      trackingRunResults = [];
    }
  }

  const tableColumns = $derived.by(() => {
    const baseColumns: Array<{ key: string; header: string; width?: string; type?: string }> = [
      { key: 'url', header: 'URL', width: '300px', type: 'link' },
      { key: 'status', header: 'Status', width: '100px', type: 'status' },
      { key: 'timestamp', header: 'Time', width: '150px' },
    ];

    if (results.length > 0) {
      const firstRow = results[0];
      const knownKeys = new Set([
        'url', 'status', 'info', 'timestamp', 'errorMessage', 'error_message',
        'screenshot_path', 'platform', 'run_id', project.urlColumn
      ]);
      for (const key of Object.keys(firstRow)) {
        if (!knownKeys.has(key)) {
          baseColumns.push({ key, header: key, width: '150px' });
        }
      }
    }
    return baseColumns;
  });
</script>

<div class={cn('space-y-4', className)}>
  <!-- Header -->
  <div class="flex items-center justify-between">
    <div class="flex items-center gap-3">
      <h2 class="text-xl font-semibold text-white m-0">{project.name}</h2>
      <Badge variant={project.platform === 'youtube' ? 'error' : 'info'} size="sm">
        {project.platform.toUpperCase()}
      </Badge>
      <span class="text-sm text-mcat-text-muted">{project.urlCount} URLs</span>
    </div>
    <div class="flex items-center gap-2">
      <Button variant="secondary" size="sm" onclick={onaddurls}>
        Add URLs
      </Button>
      <Button variant="ghost" size="sm" onclick={onclose}>
        Close
      </Button>
    </div>
  </div>

  <!-- Tracking Controls -->
  <TrackingControls />

  <!-- Progress + Controls -->
  <div class="bg-mcat-card border border-mcat-border rounded-lg p-4">
    <div class="flex flex-col gap-4">
      <div class="w-full">
        <SegmentedProgress
          counts={processing.statusCounts}
          total={processing.total || project.urlCount}
          processed={processing.processed}
          currentUrl={processing.currentUrl ?? undefined}
          showLegend={true}
        />
      </div>
      <div class="flex gap-2">
        {#if processing.isIdle}
          <Button variant="primary" size="sm" onclick={() => processing.start()}>
            Start
          </Button>
        {:else if processing.isProcessing}
          <Button variant="secondary" size="sm" onclick={() => processing.pause()}>
            Pause
          </Button>
          <Button variant="danger" size="sm" onclick={() => processing.cancel()}>
            Cancel
          </Button>
        {:else if processing.isPaused}
          <Button variant="primary" size="sm" onclick={() => processing.resume()}>
            Resume
          </Button>
          <Button variant="danger" size="sm" onclick={() => processing.cancel()}>
            Cancel
          </Button>
        {/if}
      </div>
    </div>
  </div>

  <!-- Tracking History -->
  <div class="bg-mcat-card border border-mcat-border rounded-lg p-4">
    <h3 class="text-sm font-medium mb-3">Tracking History</h3>
    <TrackingHistory onSelectRun={handleSelectTrackingRun} />
  </div>

  <!-- Results Table -->
  <div class="bg-mcat-card border border-mcat-border rounded-lg p-4">
    <div class="flex items-center justify-between mb-3">
      <h3 class="text-sm font-medium text-mcat-text m-0">
        {#if selectedTrackingRunId}
          Results ({selectedTrackingRunId}) ({trackingRunResults.length})
        {:else}
          Results ({results.length})
        {/if}
      </h3>
      {#if !selectedTrackingRunId && results.length > 0}
        <code class="text-xs text-mcat-text-muted font-mono">
          {project.combinedCsvPath}
        </code>
      {/if}
    </div>
    <DataTable
      columns={tableColumns}
      rows={selectedTrackingRunId ? trackingRunResults : results}
      maxRows={100}
      emptyMessage="No results yet. Start processing to check URLs."
      class="max-h-[300px]"
    />
  </div>

  <!-- Console -->
  <div class="bg-mcat-card border border-mcat-border rounded-lg p-4">
    <ConsolePanel
      {messages}
      maxHeight="200px"
    />
  </div>
</div>

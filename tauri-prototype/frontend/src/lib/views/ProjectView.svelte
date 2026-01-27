<script lang="ts">
  import { cn } from '$lib/utils';
  import { processingStore } from '$lib/stores/processing.svelte';
  import { consoleStore } from '$lib/stores/console.svelte';
  import Button from '$lib/components/ui/Button.svelte';
  import Badge from '$lib/components/ui/Badge.svelte';
  import Tabs from '$lib/components/ui/Tabs.svelte';
  import SegmentedProgress from '$lib/components/display/SegmentedProgress.svelte';
  import ConsolePanel from '$lib/components/display/ConsolePanel.svelte';
  import DataTable from '$lib/components/display/DataTable.svelte';
  import type { Project } from '$types/project';
  import type { ResultRow } from '$types/results';

  interface Props {
    project: Project;
    results?: ResultRow[];
    class?: string;
    onclose?: () => void;
    onaddurls?: () => void;
    onexport?: () => void;
  }

  let {
    project,
    results = [],
    class: className,
    onclose,
    onaddurls,
    onexport,
  }: Props = $props();

  const tabs = $derived([
    { value: 'processing', label: 'Processing' },
    { value: 'results', label: `Results (${results.length})` },
    { value: 'history', label: 'Run History' },
  ]);

  let activeTab = $state('processing');

  async function handleStart() {
    await processingStore.start();
    consoleStore.info('Processing started');
  }

  async function handlePause() {
    await processingStore.pause();
    consoleStore.info('Processing paused');
  }

  async function handleResume() {
    await processingStore.resume();
    consoleStore.info('Processing resumed');
  }

  async function handleCancel() {
    await processingStore.cancel();
    consoleStore.warning('Processing cancelled');
  }

  function handleClearConsole() {
    consoleStore.clear();
  }
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
      <Button variant="secondary" size="sm" onclick={onexport}>
        Export
      </Button>
      <Button variant="ghost" size="sm" onclick={onclose}>
        Close
      </Button>
    </div>
  </div>

  <!-- Processing Section -->
  <div class="bg-mcat-card border border-mcat-border rounded-lg p-6">
    <!-- Progress -->
    <SegmentedProgress
      counts={processingStore.statusCounts}
      total={processingStore.total}
      processed={processingStore.processed}
      currentUrl={processingStore.currentUrl ?? undefined}
      showLegend={processingStore.total > 0}
    />

    <!-- Stats Grid -->
    {#if processingStore.total > 0}
      <div class="grid grid-cols-4 gap-4 mt-4">
        <div class="bg-mcat-bg p-3 rounded">
          <span class="block text-xs text-mcat-text-muted mb-1">State</span>
          <span
            class={cn(
              'text-sm font-medium',
              processingStore.state === 'processing' && 'text-mcat-orange'
            )}
          >
            {processingStore.state}
          </span>
        </div>
        <div class="bg-mcat-bg p-3 rounded">
          <span class="block text-xs text-mcat-text-muted mb-1">Processed</span>
          <span class="text-sm font-medium">{processingStore.processed}</span>
        </div>
        <div class="bg-mcat-bg p-3 rounded">
          <span class="block text-xs text-mcat-text-muted mb-1">Remaining</span>
          <span class="text-sm font-medium">{processingStore.total - processingStore.processed}</span>
        </div>
        <div class="bg-mcat-bg p-3 rounded">
          <span class="block text-xs text-mcat-text-muted mb-1">Errors</span>
          <span class="text-sm font-medium text-mcat-error">{processingStore.statusCounts.error}</span>
        </div>
      </div>
    {/if}

    <!-- Controls -->
    <div class="flex gap-2 mt-4">
      {#if processingStore.isIdle}
        <Button variant="primary" onclick={handleStart}>
          Start Processing
        </Button>
      {:else if processingStore.isProcessing}
        <Button variant="secondary" onclick={handlePause}>
          Pause
        </Button>
        <Button variant="danger" onclick={handleCancel}>
          Cancel
        </Button>
      {:else if processingStore.isPaused}
        <Button variant="primary" onclick={handleResume}>
          Resume
        </Button>
        <Button variant="danger" onclick={handleCancel}>
          Cancel
        </Button>
      {/if}
    </div>
  </div>

  <!-- Tabs -->
  <Tabs {tabs} bind:value={activeTab}>
    {#snippet children(tab)}
      {#if tab === 'processing'}
        <ConsolePanel
          messages={consoleStore.messages}
          maxHeight="250px"
          onclear={handleClearConsole}
        />
      {:else if tab === 'results'}
        <DataTable
          columns={[
            { key: 'url', header: 'URL', width: '50%' },
            { key: 'status', header: 'Status', width: '100px' },
            { key: 'info', header: 'Info' },
            { key: 'timestamp', header: 'Time', width: '120px' },
          ]}
          rows={results}
          maxRows={100}
          emptyMessage="No results yet. Start processing to see results."
          class="max-h-[400px]"
        />
      {:else if tab === 'history'}
        {#if project.runs && project.runs.length > 0}
          <div class="space-y-2">
            {#each project.runs as run}
              <div class="flex items-center justify-between p-3 bg-mcat-bg rounded">
                <div class="flex items-center gap-3">
                  <span class="font-mono text-sm">{run.id}</span>
                  <Badge
                    variant={run.status === 'completed' ? 'success' : run.status === 'failed' ? 'error' : 'default'}
                    size="sm"
                  >
                    {run.status}
                  </Badge>
                </div>
                {#if run.startedAt}
                  <span class="text-sm text-mcat-text-muted">
                    {new Date(run.startedAt).toLocaleDateString()}
                  </span>
                {/if}
              </div>
            {/each}
          </div>
        {:else}
          <div class="text-center text-mcat-text-muted py-8">
            No runs yet
          </div>
        {/if}
      {/if}
    {/snippet}
  </Tabs>
</div>

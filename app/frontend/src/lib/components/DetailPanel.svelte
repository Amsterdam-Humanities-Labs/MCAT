<script lang="ts">
  import { cn } from '$lib/utils';
  import type { Run } from '$types/project';
  import { api } from '$lib/api/client';
  import { Button } from '$lib/components';
  import { Tabs } from '@mcat/ui';
  import DetailChanges from './DetailChanges.svelte';
  import DetailResults from './DetailResults.svelte';
  import DetailRun from './DetailRun.svelte';

  interface Props {
    run: Run;
    runNumber: number;
    projectPath: string;
    totalUrls: number;
    class?: string;
  }

  let { run, runNumber, projectPath, totalUrls, class: className }: Props = $props();

  let activeTab = $state(run.is_baseline ? 'results' : 'changes');

  // Changed results data (eager — small payload)
  let changedColumns = $state<string[]>([]);
  let changedRows = $state<Record<string, unknown>[]>([]);
  let changedLoading = $state(true);
  let changedError = $state<string | null>(null);

  // All results data (lazy — could be 1k+ rows)
  let resultsColumns = $state<string[]>([]);
  let resultsRows = $state<Record<string, unknown>[]>([]);
  let resultsLoading = $state(true);
  let resultsError = $state<string | null>(null);
  let resultsLoaded = $state(false);

  const tabItems = $derived(
    run.is_baseline
      ? [
          { value: 'results', label: run.total_checked > 0 ? `All Results (${run.total_checked})` : 'All Results' },
          { value: 'run', label: 'Run Info' },
        ]
      : [
          { value: 'changes', label: changedRows.length > 0 ? `Changes (${changedRows.length})` : 'Changes' },
          { value: 'results', label: run.total_checked > 0 ? `All Results (${run.total_checked})` : 'All Results' },
          { value: 'run', label: 'Run Info' },
        ]
  );

  // Load changed results eagerly
  $effect(() => {
    if (run.is_baseline) {
      changedLoading = false;
      return;
    }
    changedLoading = true;
    changedError = null;
    api.getRunChangedResults(run.id)
      .then((res) => { changedColumns = res.columns; changedRows = res.rows; })
      .catch((e) => { changedError = String(e); })
      .finally(() => { changedLoading = false; });
  });

  // Load all results lazily
  $effect(() => {
    if (activeTab !== 'results' || resultsLoaded) return;
    resultsLoading = true;
    resultsError = null;
    api.getRunResults(run.id)
      .then((res) => { resultsColumns = res.columns; resultsRows = res.rows; resultsLoaded = true; })
      .catch((e) => { resultsError = String(e); })
      .finally(() => { resultsLoading = false; });
  });

  async function handleOpenFolder() {
    try {
      await api.openExternal(`${projectPath}/runs/${run.id}`);
    } catch {
      // ignore
    }
  }

  async function handleOpenScreenshot(path: string) {
    try {
      await api.openExternal(path);
    } catch {
      // ignore
    }
  }
</script>

<div class={cn("bg-bg-primary overflow-auto max-h-[800px] shadow-[0_8px_12px_-4px_rgba(0,0,0,0.2)] relative z-10 border-b border-border-light", className)}>
  <!-- Header: Run #N | Tabs | Run Folder -->
  <div class="flex items-center gap-3 px-4 py-2">
    <span class="text-base text-text-primary shrink-0">Run #{runNumber}</span>

    <Tabs tabs={tabItems} bind:value={activeTab} />

    <div class="ml-auto shrink-0">
      <Button variant="secondary" onclick={handleOpenFolder}>
        Run Folder
      </Button>
    </div>
  </div>

  <!-- Tab content -->
  <div class="px-4 pb-2">
    {#if activeTab === 'changes'}
      <DetailChanges {run} columns={changedColumns} rows={changedRows} loading={changedLoading} error={changedError} onOpenScreenshot={handleOpenScreenshot} />
    {:else if activeTab === 'results'}
      <DetailResults columns={resultsColumns} rows={resultsRows} loading={resultsLoading} error={resultsError} onOpenScreenshot={handleOpenScreenshot} />
    {:else if activeTab === 'run'}
      <DetailRun {run} {runNumber} {totalUrls} />
    {/if}
  </div>
</div>

<script lang="ts">
  import { cn } from '$lib/utils';
  import type { Run } from '$types/project';
  import { api } from '$lib/api/client';
  import { runDetailsStore } from '$lib/stores/runDetails.svelte';
  import { Button } from '$lib/components';
  import { Tabs } from '@mcat/shared-ui';
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

  // Both payloads live in the store, so they survive this panel being collapsed.
  const changed = $derived(runDetailsStore.changes(projectPath, run.id));
  const results = $derived(runDetailsStore.results(projectPath, run.id));
  const changedRows = $derived(changed?.rows ?? []);

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

  // Eager: small payload. The store no-ops when it is already cached.
  $effect(() => {
    if (!run.is_baseline) runDetailsStore.loadChanges(projectPath, run.id);
  });

  // Lazy: a run can be 1k+ rows, so only fetch once its tab is opened.
  $effect(() => {
    if (activeTab === 'results') runDetailsStore.loadResults(projectPath, run.id);
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
      <DetailChanges
        {run}
        columns={changed?.columns ?? []}
        rows={changedRows}
        loading={changed?.loading ?? true}
        error={changed?.error ?? null}
        onOpenScreenshot={handleOpenScreenshot}
      />
    {:else if activeTab === 'results'}
      <DetailResults
        columns={results?.columns ?? []}
        rows={results?.rows ?? []}
        loading={results?.loading ?? true}
        error={results?.error ?? null}
        onOpenScreenshot={handleOpenScreenshot}
      />
    {:else if activeTab === 'run'}
      <DetailRun {run} {runNumber} {totalUrls} />
    {/if}
  </div>
</div>

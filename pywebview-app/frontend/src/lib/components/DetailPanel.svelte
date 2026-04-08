<script lang="ts">
  import { cn } from '$lib/utils';
  import type { Run } from '$types/project';
  import { api } from '$lib/api/client';
  import DetailHeader from './DetailHeader.svelte';
  import Tabs from './Tabs.svelte';
  import DetailChanges from './DetailChanges.svelte';
  import DetailResults from './DetailResults.svelte';
  import DetailRun from './DetailRun.svelte';

  interface Change {
    url: string;
    previous_status: string;
    new_status: string;
    timestamp: string;
    screenshot_path: string;
  }

  interface Props {
    run: Run;
    runNumber: number;
    projectPath: string;
    totalUrls: number;
    class?: string;
  }

  let { run, runNumber, projectPath, totalUrls, class: className }: Props = $props();

  let activeTab = $state('changes');

  const tabItems = [
    { value: 'changes', label: 'Changes' },
    { value: 'results', label: 'All Results' },
    { value: 'run', label: 'Run' },
  ];

  // Changes data
  let changes = $state<Change[]>([]);
  let changesLoading = $state(true);
  let changesError = $state<string | null>(null);

  // Results data
  let resultsColumns = $state<string[]>([]);
  let resultsRows = $state<Record<string, unknown>[]>([]);
  let resultsLoading = $state(true);
  let resultsError = $state<string | null>(null);
  let resultsLoaded = $state(false);

  // Load changes on mount
  $effect(() => {
    if (run.is_baseline) {
      changesLoading = false;
      return;
    }
    changesLoading = true;
    changesError = null;
    api.getRunChanges(run.id)
      .then((res) => { changes = res.changes; })
      .catch((e) => { changesError = String(e); })
      .finally(() => { changesLoading = false; });
  });

  // Load results lazily on tab switch
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

<div class={cn("bg-bg-detail overflow-auto max-h-[400px] border-t border-border-mid", className)}>
  <div class="flex gap-1 px-4">
    <div class="w-5 shrink-0"></div>
    <div class="flex-1 min-w-0">
      <DetailHeader onOpenFolder={handleOpenFolder} />
    </div>
  </div>

  <Tabs tabs={tabItems} bind:value={activeTab}>
    {#snippet children(tab)}
      <div class="flex gap-1 px-4">
        <div class="w-5 shrink-0"></div>
        <div class="flex-1 min-w-0">
          {#if tab === 'changes'}
            <DetailChanges {run} {changes} loading={changesLoading} error={changesError} onOpenScreenshot={handleOpenScreenshot} />
          {:else if tab === 'results'}
            <DetailResults columns={resultsColumns} rows={resultsRows} loading={resultsLoading} error={resultsError} />
          {:else if tab === 'run'}
            <DetailRun {run} {runNumber} {totalUrls} />
          {/if}
        </div>
      </div>
    {/snippet}
  </Tabs>
</div>

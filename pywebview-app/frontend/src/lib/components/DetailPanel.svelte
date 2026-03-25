<script lang="ts">
  import type { Run } from '$types/project';
  import { api } from '$lib/api/client';
  import DetailHeader from './DetailHeader.svelte';
  import DetailTabs from './DetailTabs.svelte';
  import DetailChanges from './DetailChanges.svelte';
  import DetailResults from './DetailResults.svelte';

  interface Change {
    url: string;
    previous_status: string;
    new_status: string;
    timestamp: string;
  }

  interface Props {
    run: Run;
    runNumber: number;
    projectPath: string;
  }

  let { run, runNumber, projectPath }: Props = $props();

  let activeTab = $state<'changes' | 'results'>('changes');

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
</script>

<div class="bg-bg-primary border-t border-border-light ml-10 mr-4 overflow-auto max-h-[400px]">
  <div class="px-4">
    <DetailHeader {run} {runNumber} onOpenFolder={handleOpenFolder} />
    <DetailTabs {activeTab} onchange={(tab) => (activeTab = tab)} />

    {#if activeTab === 'changes'}
      <DetailChanges {run} {changes} loading={changesLoading} error={changesError} />
    {:else}
      <DetailResults columns={resultsColumns} rows={resultsRows} loading={resultsLoading} error={resultsError} />
    {/if}
  </div>
</div>

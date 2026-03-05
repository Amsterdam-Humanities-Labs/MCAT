<script lang="ts">
  import { onMount } from 'svelte';
  import { api } from '$lib/api/client';
  import { projectStore } from '$lib/stores/project.svelte';
  import { Select } from '$lib/components';

  interface Props {
    onSelectRun?: (runId: string) => void;
  }

  let { onSelectRun }: Props = $props();

  let runs = $state<Array<{ value: string; label: string }>>([]);
  let selectedRunId = $state<string | null>(null);
  let isLoading = $state(false);

  onMount(async () => {
    // Get the project to access runs
    const project = projectStore.project;
    if (!project) return;

    try {
      isLoading = true;

      // Extract tracking runs from project data
      if (project && project.runs) {
        const trackingRuns = project.runs
          .filter((r: any) => r.id.startsWith('TRACK-'))
          .sort((a: any, b: any) => new Date(b.startedAt || 0).getTime() - new Date(a.startedAt || 0).getTime())
          .map((r: any) => ({
            value: r.id,
            label: `${r.id} - ${r.startedAt ? new Date(r.startedAt).toLocaleString() : 'Unknown time'}`
          }));

        runs = trackingRuns;
      }
    } finally {
      isLoading = false;
    }
  });

  function handleSelectRun(runId: string | null) {
    selectedRunId = runId;
    if (runId) {
      onSelectRun?.(runId);
    }
  }
</script>

<div class="tracking-history space-y-3">
  {#if runs.length === 0}
    <p class="text-sm text-mcat-text-muted">No tracking runs yet. Start tracking to monitor URLs.</p>
  {:else}
    <div class="flex items-center gap-2">
      <span class="text-sm text-mcat-text-muted">View tracking run:</span>
      <Select
        bind:value={selectedRunId}
        options={runs}
        placeholder="Select a tracking run..."
        disabled={isLoading}
        onchange={() => handleSelectRun(selectedRunId)}
      />
    </div>
  {/if}
</div>

<style>
  .tracking-history :global(select) {
    flex: 1;
    max-width: 400px;
  }
</style>

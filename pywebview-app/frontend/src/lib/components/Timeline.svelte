<script lang="ts">
  import type { Run } from '$types/project';
  import TimelineAxis from './TimelineAxis.svelte';
  import TimelineRow from './TimelineRow.svelte';
  import TimelineRunning from './TimelineRunning.svelte';
  import DetailPanel from './DetailPanel.svelte';

  interface ActiveRun {
    timestamp: string;
    progressPercent: number;
  }

  interface Props {
    runs: Run[];
    currentRun: ActiveRun | null;
    selectedRunId: string | null;
    projectPath: string;
    onRunClick?: (id: string) => void;
  }

  let { runs, currentRun, selectedRunId, projectPath, onRunClick }: Props = $props();

  let scrollContainer: HTMLDivElement | undefined = $state();

  const sortedRuns = $derived(
    runs
      .filter((r) => r.status === 'completed' || r.status === 'abandoned')
      .sort((a, b) => new Date(a.started_at).getTime() - new Date(b.started_at).getTime())
  );

  const runCount = $derived(sortedRuns.length + (currentRun ? 1 : 0));

  // Auto-scroll to bottom when runs change
  $effect(() => {
    if (scrollContainer && runCount > 0) {
      setTimeout(() => {
        if (scrollContainer) {
          scrollContainer.scrollTop = scrollContainer.scrollHeight;
        }
      }, 50);
    }
  });

  function getRunNumber(index: number): number {
    return index + 1;
  }
</script>

{#if sortedRuns.length > 0 || currentRun}
  <div class="flex-1 flex flex-col overflow-hidden bg-bg-timeline">
    <div class="px-4 pt-3 pb-1">
      <span class="text-text-secondary font-bold text-sm tracking-wider">RUNS</span>
    </div>

    <div
      bind:this={scrollContainer}
      class="flex-1 overflow-y-auto relative"
    >
      <TimelineAxis />

      <div class="flex flex-col">
        {#each sortedRuns as run, i (run.id)}
          <TimelineRow
            {run}
            index={i}
            isSelected={selectedRunId === run.id}
            onClick={() => onRunClick?.(run.id)}
          />

          {#if selectedRunId === run.id}
            <DetailPanel
              {run}
              runNumber={getRunNumber(i)}
              {projectPath}
            />
          {/if}
        {/each}

        {#if currentRun}
          <TimelineRunning
            timestamp={currentRun.timestamp}
            progressPercent={currentRun.progressPercent}
          />
        {/if}
      </div>
    </div>
  </div>
{/if}

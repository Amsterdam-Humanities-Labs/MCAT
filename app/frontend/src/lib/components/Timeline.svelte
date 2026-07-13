<script lang="ts">
  import { cn } from '$lib/utils';
  import type { Run } from '$types/project';
  import TimelineRow from './TimelineRow.svelte';
  import TimelineRunning from './TimelineRunning.svelte';
  import DetailPanel from './DetailPanel.svelte';

  interface ActiveRun {
    timestamp: string;
    paused: boolean;
  }

  interface Props {
    runs: Run[];
    currentRun: ActiveRun | null;
    selectedRunId: string | null;
    projectPath: string;
    totalUrls: number;
    onRunClick?: (id: string) => void;
    class?: string;
  }

  let { runs, currentRun, selectedRunId, projectPath, totalUrls, onRunClick, class: className }: Props = $props();

  const sortedRuns = $derived(
    runs
      .filter((r) => r.status === 'completed' || r.status === 'abandoned')
      .sort((a, b) => new Date(b.started_at).getTime() - new Date(a.started_at).getTime())
  );

</script>

<div class={cn("flex-1 flex flex-col overflow-hidden bg-bg-timeline min-h-0", className)}>
  <div class="flex-1 overflow-y-auto">
    <div class="flex flex-col">
      {#if currentRun}
        <TimelineRunning
          timestamp={currentRun.timestamp}
          paused={currentRun.paused}
        />
      {/if}

      {#each sortedRuns as run, i (run.id)}
        <TimelineRow
          {run}
          isSelected={selectedRunId === run.id}
          onClick={() => onRunClick?.(run.id)}
        />

        {#if selectedRunId === run.id}
          <DetailPanel
            {run}
            runNumber={sortedRuns.length - i}
            {projectPath}
            {totalUrls}
          />
        {/if}
      {/each}
    </div>
  </div>
</div>

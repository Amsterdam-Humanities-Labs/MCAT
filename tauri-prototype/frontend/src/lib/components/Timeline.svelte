<script lang="ts">
  import type { Run } from '$types/project';
  import TimelineAxis from './TimelineAxis.svelte';
  import TimelineDot from './TimelineDot.svelte';
  import TimelineRunning from './TimelineRunning.svelte';

  interface ActiveRun {
    timestamp: string;
    progressPercent: number;
  }

  interface Props {
    runs: Run[];
    currentRun: ActiveRun | null;
    selectedRunId: string | null;
    onRunClick?: (id: string) => void;
  }

  let { runs, currentRun, selectedRunId, onRunClick }: Props = $props();

  let scrollContainer: HTMLDivElement | undefined = $state();

  const DOT_GAP = 200;

  const completedRuns = $derived(
    runs
      .filter((r) => r.status === 'completed')
      .sort((a, b) => new Date(a.startedAt).getTime() - new Date(b.startedAt).getTime())
  );

  const dotCount = $derived(completedRuns.length + (currentRun ? 1 : 0));
  const totalWidth = $derived(Math.max(800, dotCount * DOT_GAP + 100));

  // Auto-scroll to right end when runs change
  $effect(() => {
    if (scrollContainer && dotCount > 0) {
      // Use setTimeout to ensure DOM is updated
      setTimeout(() => {
        if (scrollContainer) {
          scrollContainer.scrollLeft = scrollContainer.scrollWidth;
        }
      }, 50);
    }
  });
</script>

{#if completedRuns.length > 0 || currentRun}
  <div class="bg-bg-timeline border-b border-border-light">
    <div class="px-4 pt-3 pb-1">
      <span class="text-text-secondary font-bold text-[14px] tracking-wider">RUNS</span>
    </div>
    <div
      bind:this={scrollContainer}
      class="overflow-x-auto pb-4"
    >
      <div class="relative" style="width: {totalWidth}px; min-height: 160px;">
        <!-- Axis line positioned at dot center height -->
        <div class="absolute left-8 right-0" style="top: 26px;">
          <TimelineAxis width={totalWidth - 40} />
        </div>

        <!-- Dots -->
        <div class="relative flex items-start gap-0 px-8" style="top: 12px;">
          {#each completedRuns as run, i (run.id)}
            <div style="min-width: {DOT_GAP}px; flex-shrink: 0;">
              <TimelineDot
                {run}
                isSelected={selectedRunId === run.id}
                onClick={() => onRunClick?.(run.id)}
              />
            </div>
          {/each}

          {#if currentRun}
            <div style="min-width: {DOT_GAP}px; flex-shrink: 0;">
              <TimelineRunning
                timestamp={currentRun.timestamp}
                progressPercent={currentRun.progressPercent}
              />
            </div>
          {/if}
        </div>
      </div>
    </div>
  </div>
{/if}

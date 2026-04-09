<script lang="ts">
  import { cn } from '$lib/utils';
  import type { RunStatusSummary } from '$types/project';

  interface Props {
    statusCounts: RunStatusSummary;
    baselineCounts: RunStatusSummary | null;
    class?: string;
  }

  let { statusCounts, baselineCounts, class: className }: Props = $props();

  function formatDelta(current: number, baseline: number | undefined): string {
    if (baseline === undefined) return '';
    const diff = current - baseline;
    if (diff === 0) return '';
    return diff > 0 ? `+${diff}` : `${diff}`;
  }

  const items = $derived([
    { label: 'Live', count: statusCounts.live, delta: formatDelta(statusCounts.live, baselineCounts?.live), color: 'bg-status-live', textColor: 'text-status-live' },
    { label: 'Removed', count: statusCounts.removed, delta: formatDelta(statusCounts.removed, baselineCounts?.removed), color: 'bg-status-removed', textColor: 'text-status-removed' },
    { label: 'Restricted', count: statusCounts.restricted, delta: formatDelta(statusCounts.restricted, baselineCounts?.restricted), color: 'bg-status-restricted', textColor: 'text-status-restricted' },
    { label: 'Error', count: statusCounts.error, delta: formatDelta(statusCounts.error, baselineCounts?.error), color: 'bg-status-error', textColor: 'text-status-error' },
  ]);
</script>

<div class={cn("flex items-center gap-4", className)}>
  {#each items as item (item.label)}
    <div class="flex items-center gap-1.5">
      <span class="w-2.5 h-2.5 rounded-full {item.color}"></span>
      <span class="text-text-secondary">{item.count.toLocaleString()} {item.label}</span>
      {#if item.delta}
        <span class="{item.textColor} text-base">({item.delta})</span>
      {/if}
    </div>
  {/each}
</div>

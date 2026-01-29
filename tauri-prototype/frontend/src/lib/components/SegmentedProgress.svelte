<script lang="ts">
  import { cn } from '$lib/utils';
  import type { StatusCounts } from '$types/results';

  interface Props {
    counts: StatusCounts;
    total: number;
    processed: number;
    currentUrl?: string;
    showLegend?: boolean;
    class?: string;
  }

  let {
    counts,
    total,
    processed,
    currentUrl,
    showLegend = true,
    class: className,
  }: Props = $props();

  const statusColors = {
    live: 'bg-status-live',
    removed: 'bg-status-removed',
    restricted: 'bg-status-restricted',
    error: 'bg-status-error',
    pending: 'bg-status-pending',
  };

  const statusLabels = {
    live: 'Live',
    removed: 'Removed',
    restricted: 'Restricted',
    error: 'Error',
    pending: 'Pending',
  };

  const segments = $derived(
    (['live', 'removed', 'restricted', 'error', 'pending'] as const).map((status) => ({
      status,
      count: counts[status],
      percentage: total > 0 ? (counts[status] / total) * 100 : 0,
      color: statusColors[status],
      label: statusLabels[status],
    }))
  );

  const progressPercentage = $derived(total > 0 ? Math.round((processed / total) * 100) : 0);
</script>

<div class={cn('w-full', className)}>
  <!-- Progress bar -->
  <div class="h-4 bg-mcat-border rounded-full overflow-hidden flex">
    {#each segments as segment}
      {#if segment.percentage > 0}
        <div
          class={cn('h-full transition-all duration-300', segment.color)}
          style="width: {segment.percentage}%"
          title="{segment.label}: {segment.count}"
        ></div>
      {/if}
    {/each}
  </div>

  <!-- Stats row -->
  <div class="mt-2 flex items-center justify-between text-sm">
    <span class="text-mcat-text-muted">
      {processed} / {total} ({progressPercentage}%)
    </span>
    {#if currentUrl}
      <span class="text-mcat-text-muted truncate max-w-[60%]" title={currentUrl}>
        {currentUrl}
      </span>
    {/if}
  </div>

  <!-- Legend -->
  {#if showLegend}
    <div class="mt-3 flex flex-wrap gap-4">
      {#each segments as segment}
        <div class="flex items-center gap-1.5">
          <div class={cn('w-3 h-3 rounded-sm', segment.color)}></div>
          <span class="text-xs text-mcat-text-muted">
            {segment.label}: {segment.count}
          </span>
        </div>
      {/each}
    </div>
  {/if}
</div>

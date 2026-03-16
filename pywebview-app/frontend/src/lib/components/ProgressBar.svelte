<script lang="ts">
  import type { RunStatusSummary } from '$types/project';

  interface Props {
    total: number;
    statusCounts: RunStatusSummary;
  }

  let { total, statusCounts }: Props = $props();

  const segments = $derived([
    { key: 'live', count: statusCounts.live, color: 'bg-status-live' },
    { key: 'removed', count: statusCounts.removed, color: 'bg-status-removed' },
    { key: 'restricted', count: statusCounts.restricted, color: 'bg-status-restricted' },
    { key: 'error', count: statusCounts.error, color: 'bg-status-error' },
  ]);
</script>

<div class="h-1.5 rounded-full bg-progress-track overflow-hidden flex">
  {#each segments as seg (seg.key)}
    {#if seg.count > 0 && total > 0}
      <div
        class="h-full {seg.color}"
        style="width: {(seg.count / total) * 100}%"
      ></div>
    {/if}
  {/each}
</div>

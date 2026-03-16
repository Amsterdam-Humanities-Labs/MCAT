<script lang="ts">
  import type { RunStatusSummary } from '$types/project';

  interface Props {
    statusCounts: RunStatusSummary;
  }

  let { statusCounts }: Props = $props();

  const items = $derived([
    { label: 'Live', count: statusCounts.live, color: 'bg-status-live' },
    { label: 'Removed', count: statusCounts.removed, color: 'bg-status-removed' },
    { label: 'Restricted', count: statusCounts.restricted, color: 'bg-status-restricted' },
    { label: 'Error', count: statusCounts.error, color: 'bg-status-error' },
  ]);
</script>

<div class="flex items-center gap-4">
  {#each items as item (item.label)}
    <div class="flex items-center gap-1.5">
      <span class="w-2.5 h-2.5 rounded-full {item.color}"></span>
      <span class="text-text-secondary">{item.count.toLocaleString()} {item.label}</span>
    </div>
  {/each}
</div>

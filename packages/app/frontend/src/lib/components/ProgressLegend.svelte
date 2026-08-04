<script lang="ts">
  import { cn } from '$lib/utils';
  import { STATUS_META, StatusBadge } from '@mcat/shared-ui';
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

  const items = $derived(
    STATUS_META.map((m) => ({
      status: m.key,
      label: m.label,
      count: statusCounts[m.summaryKey],
      delta: formatDelta(statusCounts[m.summaryKey], baselineCounts?.[m.summaryKey]),
      textColor: m.text,
    }))
  );
</script>

<div class={cn("flex items-center gap-4", className)}>
  {#each items as item (item.label)}
    <div class="flex items-center gap-1.5">
      <StatusBadge status={item.status} size="sm" />
      <span class="text-text-secondary">{item.count.toLocaleString()} {item.label}</span>
      {#if item.delta}
        <span class="{item.textColor} text-base">({item.delta})</span>
      {/if}
    </div>
  {/each}
</div>

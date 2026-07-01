<script lang="ts">
  import { cn } from '$lib/utils';
  import { STATUS_META } from '$lib/status';
  import type { RunStatusSummary } from '$types/project';

  interface Props {
    total: number;
    statusCounts: RunStatusSummary;
    class?: string;
  }

  let { total, statusCounts, class: className }: Props = $props();

  const segments = $derived(
    STATUS_META.map((m) => ({ key: m.key, count: statusCounts[m.summaryKey], color: m.bg }))
  );
</script>

<div class={cn("h-1.5 rounded bg-progress-track overflow-hidden flex", className)}>
  {#each segments as seg (seg.key)}
    {#if seg.count > 0 && total > 0}
      <div
        class="h-full {seg.color}"
        style="width: {(seg.count / total) * 100}%"
      ></div>
    {/if}
  {/each}
</div>

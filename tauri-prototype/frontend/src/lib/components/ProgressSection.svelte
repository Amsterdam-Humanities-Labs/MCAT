<script lang="ts">
  import type { RunStatusSummary } from '$types/project';
  import ProgressBar from './ProgressBar.svelte';
  import ProgressLegend from './ProgressLegend.svelte';

  interface Props {
    total: number;
    checked: number;
    statusCounts: RunStatusSummary;
  }

  let { total, checked, statusCounts }: Props = $props();

  const pct = $derived(total > 0 ? Math.round((checked / total) * 100) : 0);
  const hasData = $derived(checked > 0 || total > 0);
</script>

{#if hasData}
  <div class="px-4 py-3 border-b border-border-mid">
    <ProgressBar {total} {statusCounts} />
    <div class="mt-2 flex items-center gap-4">
      <span class="text-text-body">
        {checked.toLocaleString()} / {total.toLocaleString()} ({pct}%)
      </span>
      <ProgressLegend {statusCounts} />
    </div>
  </div>
{/if}

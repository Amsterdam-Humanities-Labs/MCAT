<script lang="ts">
  import { cn } from '$lib/utils';
  import type { Run } from '$types/project';
  import { formatTimestamp, formatDuration } from '$lib/utils/format';

  interface Props {
    run: Run;
    runNumber: number;
    totalUrls: number;
    class?: string;
  }

  let { run, runNumber, totalUrls, class: className }: Props = $props();

  const statusLabel = $derived.by(() => {
    if (run.status === 'abandoned') return 'Abandoned';
    if (run.status === 'in_progress') return 'Running';
    return 'Completed';
  });

  const rows = $derived.by(() => {
    const items: Array<{ label: string; value: string }> = [
      { label: 'Run', value: `#${runNumber}` },
      { label: 'Status', value: statusLabel },
      ...(run.status === 'abandoned' && run.total_checked > 0
        ? [{ label: 'Processed URLs', value: `${run.total_checked} / ${totalUrls}` }]
        : []),
      { label: 'Started', value: formatTimestamp(run.started_at) },
    ];
    if (run.completed_at) {
      items.push({ label: 'Completed', value: formatTimestamp(run.completed_at) });
    }
    if (run.duration_seconds > 0) {
      items.push({ label: 'Duration', value: formatDuration(run.duration_seconds) });
    }
    if (run.total_checked > 0) {
      items.push({ label: 'URLs checked', value: run.total_checked.toLocaleString() });
    }
    if (run.changes_count > 0) {
      items.push({ label: 'Changes', value: run.changes_count.toLocaleString() });
    }
    if (run.is_baseline) {
      items.push({ label: 'Type', value: 'Baseline' });
    }
    return items;
  });
</script>

<div class={cn("py-3 text-base", className)}>
  <div class="flex flex-col gap-1.5">
    {#each rows as row}
      <div class="flex gap-4">
        <span class="text-text-muted whitespace-nowrap shrink-0">{row.label}</span>
        <span class="text-text-body">{row.value}</span>
      </div>
    {/each}
  </div>
</div>

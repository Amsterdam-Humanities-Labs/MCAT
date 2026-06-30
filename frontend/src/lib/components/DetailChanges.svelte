<script lang="ts">
  import { cn } from '$lib/utils';
  import type { Run } from '$types/project';
  import { colors } from '$lib/theme';
  import { normalizeRows, buildResultColumns } from '$lib/utils/resultTable';
  import DataTable from './DataTable.svelte';

  interface Props {
    run: Run;
    columns: string[];
    rows: Record<string, unknown>[];
    loading: boolean;
    error: string | null;
    onOpenScreenshot?: (path: string) => void;
    class?: string;
  }

  let { run, columns, rows, loading, error, onOpenScreenshot, class: className }: Props = $props();

  const displayRows = $derived(normalizeRows(rows));
  const tableColumns = $derived(buildResultColumns(columns, { statusType: 'transition', internal: ['previous_status'] }));
</script>

<div class={cn(className)}>
{#if loading}
  <p class="text-text-secondary text-base py-4">Loading...</p>
{:else if error}
  <p class="text-status-removed text-base py-4">{error}</p>
{:else if run.is_baseline}
  <div class="py-3 text-base">
    <p class="text-text-secondary mb-2">Baseline run — initial status of all URLs:</p>
    <div class="flex items-center gap-3">
      {#if run.status_summary?.live}
        <span style="color: {colors.status.live}">{run.status_summary.live} Live</span>
      {/if}
      {#if run.status_summary?.restricted}
        <span style="color: {colors.status.restricted}">{run.status_summary.restricted} Restricted</span>
      {/if}
      {#if run.status_summary?.moderated}
        <span style="color: {colors.status.moderated}">{run.status_summary.moderated} Moderated</span>
      {/if}
      {#if run.status_summary?.unavailable}
        <span style="color: {colors.status.unavailable}">{run.status_summary.unavailable} Unavailable</span>
      {/if}
    </div>
  </div>
{:else}
  <DataTable columns={tableColumns} rows={displayRows} emptyMessage="No changes detected" onScreenshotClick={onOpenScreenshot} />
{/if}
</div>

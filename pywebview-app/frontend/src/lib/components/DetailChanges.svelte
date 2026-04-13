<script lang="ts">
  import { cn } from '$lib/utils';
  import type { Run } from '$types/project';
  import { colors } from '$lib/theme';
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

  const INTERNAL_COLUMNS = ['previous_status', 'screenshot_path'];

  const urlColumn = $derived(columns.find(c => !INTERNAL_COLUMNS.includes(c) && c !== 'status'));

  const tableColumns = $derived.by(() => {
    if (!urlColumn) return [];
    const rest = columns.filter(c => c !== urlColumn && c !== 'status' && !INTERNAL_COLUMNS.includes(c));
    const ordered = [urlColumn, 'status', ...rest];

    return ordered.map((col) => ({
      key: col,
      header: col === 'status' ? 'change' : col,
      type: col === 'status' ? 'transition' as const : col === urlColumn ? 'link' as const : 'text' as const,
    }));
  });
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
      {#if run.status_summary?.removed}
        <span style="color: {colors.status.removed}">{run.status_summary.removed} Removed</span>
      {/if}
    </div>
  </div>
{:else}
  <DataTable columns={tableColumns} {rows} emptyMessage="No changes detected" onScreenshotClick={onOpenScreenshot} />
{/if}
</div>

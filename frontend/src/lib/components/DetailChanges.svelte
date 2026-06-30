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

  const INTERNAL_COLUMNS = ['previous_status'];
  // Desired column order: url, then these mcat columns; anything else trails.
  const MCAT_ORDER = ['mcat_status', 'mcat_screenshot', 'mcat_user', 'mcat_detail', 'mcat_error'];

  const naCell = (v: unknown): string => {
    const s = v == null ? '' : String(v).trim();
    return s === '' || s.toUpperCase() === 'N/A' ? 'n/a' : s;
  };

  const mcatIndex = (r: Record<string, unknown>): number => {
    const n = Number(r.mcat_index);
    return Number.isFinite(n) ? n : Infinity;
  };

  const displayRows = $derived(rows.map((r) => {
    const out = { ...r };
    if ('mcat_detail' in out) out.mcat_detail = naCell(out.mcat_detail);
    if ('mcat_error' in out) out.mcat_error = naCell(out.mcat_error);
    return out;
  }).sort((a, b) => mcatIndex(a) - mcatIndex(b)));

  const urlColumn = $derived(columns.find(c => !INTERNAL_COLUMNS.includes(c) && c !== 'mcat_status' && !c.startsWith('mcat_')));

  const tableColumns = $derived.by(() => {
    if (!urlColumn) return [];
    const head = ['mcat_index', urlColumn, ...MCAT_ORDER].filter(c => columns.includes(c) && !INTERNAL_COLUMNS.includes(c));
    const rest = columns.filter(c => !head.includes(c) && !INTERNAL_COLUMNS.includes(c));

    return [...head, ...rest].map((col) => ({
      key: col,
      header: col === 'mcat_status' ? 'change' : col === 'mcat_index' ? '#' : col,
      type: col === 'mcat_status' ? 'transition' as const : col === urlColumn ? 'link' as const : col === 'mcat_screenshot' ? 'file' as const : 'text' as const,
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

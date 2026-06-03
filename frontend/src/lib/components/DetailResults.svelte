<script lang="ts">
  import { cn } from '$lib/utils';
  import DataTable from './DataTable.svelte';

  interface Props {
    columns: string[];
    rows: Record<string, unknown>[];
    loading: boolean;
    error: string | null;
    onOpenScreenshot?: (path: string) => void;
    class?: string;
  }

  let { columns, rows, loading, error, onOpenScreenshot, class: className }: Props = $props();

  // Desired column order: url, then these mcat columns; anything else trails.
  const MCAT_ORDER = ['mcat_status', 'mcat_screenshot', 'mcat_user', 'mcat_detail', 'mcat_error'];

  const naCell = (v: unknown): string => {
    const s = v == null ? '' : String(v).trim();
    return s === '' || s.toUpperCase() === 'N/A' ? 'n/a' : s;
  };

  const displayRows = $derived(rows.map((r) => {
    const out = { ...r };
    if ('mcat_detail' in out) out.mcat_detail = naCell(out.mcat_detail);
    if ('mcat_error' in out) out.mcat_error = naCell(out.mcat_error);
    return out;
  }));

  const tableColumns = $derived.by(() => {
    const urlCol = columns.find(c => c !== 'mcat_status' && !c.startsWith('mcat_'));
    if (!urlCol) return columns.map(c => ({ key: c, header: c, type: 'text' as const }));

    const head = [urlCol, ...MCAT_ORDER].filter(c => columns.includes(c));
    const rest = columns.filter(c => !head.includes(c));

    return [...head, ...rest].map((col) => ({
      key: col,
      header: col,
      type: col === 'mcat_status' ? 'status' as const : col === urlCol ? 'link' as const : col === 'mcat_screenshot' ? 'file' as const : 'text' as const,
    }));
  });
</script>

<div class={cn(className)}>
{#if loading}
  <p class="text-text-secondary text-base py-4">Loading...</p>
{:else if error}
  <p class="text-status-removed text-base py-4">{error}</p>
{:else}
  <DataTable columns={tableColumns} rows={displayRows} onScreenshotClick={onOpenScreenshot} />
{/if}
</div>

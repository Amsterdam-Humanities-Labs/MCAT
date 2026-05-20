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

  const HIDDEN_COLUMNS = ['mcat_screenshot'];

  const tableColumns = $derived.by(() => {
    const urlCol = columns.find(c => c !== 'mcat_status' && !c.startsWith('mcat_'));
    if (!urlCol) return columns.filter(c => !HIDDEN_COLUMNS.includes(c)).map(c => ({
      key: c, header: c, type: 'text' as const,
    }));

    const rest = columns.filter(c => c !== urlCol && c !== 'mcat_status' && !HIDDEN_COLUMNS.includes(c));
    const ordered = [urlCol, 'mcat_status', ...rest];

    return ordered.map((col) => ({
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
  <DataTable columns={tableColumns} {rows} onScreenshotClick={onOpenScreenshot} />
{/if}
</div>

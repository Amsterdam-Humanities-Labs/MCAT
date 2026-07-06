<script lang="ts">
  import { cn } from '$lib/utils';
  import { normalizeRows, buildResultColumns } from '$lib/utils/resultTable';
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

  const displayRows = $derived(normalizeRows(rows));
  const tableColumns = $derived(buildResultColumns(columns, { statusType: 'status' }));
</script>

<div class={cn(className)}>
{#if loading}
  <p class="text-text-secondary text-base py-4">Loading...</p>
{:else if error}
  <p class="text-status-removed text-base py-4">{error}</p>
{:else}
  <DataTable columns={tableColumns} rows={displayRows} maxRows={displayRows.length} onScreenshotClick={onOpenScreenshot} />
{/if}
</div>

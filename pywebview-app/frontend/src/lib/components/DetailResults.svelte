<script lang="ts">
  import { cn } from '$lib/utils';
  import DataTable from './DataTable.svelte';

  interface Props {
    columns: string[];
    rows: Record<string, unknown>[];
    loading: boolean;
    error: string | null;
    class?: string;
  }

  let { columns, rows, loading, error, class: className }: Props = $props();

  const tableColumns = $derived(
    columns.map((col) => ({
      key: col,
      header: col,
      type: col === 'status' ? 'status' as const : col.toLowerCase().includes('url') ? 'link' as const : 'text' as const,
    }))
  );
</script>

<div class={cn(className)}>
{#if loading}
  <p class="text-text-muted text-sm py-4">Loading...</p>
{:else if error}
  <p class="text-status-removed text-sm py-4">{error}</p>
{:else}
  <div class="py-3">
    <DataTable columns={tableColumns} {rows} />
  </div>
{/if}
</div>

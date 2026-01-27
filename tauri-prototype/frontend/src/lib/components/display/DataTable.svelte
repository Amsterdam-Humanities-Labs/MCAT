<script lang="ts" generics="T">
  import { cn } from '$lib/utils';

  interface Column<T> {
    key: keyof T | string;
    header: string;
    width?: string;
  }

  interface Props {
    columns: Column<T>[];
    rows: T[];
    maxRows?: number;
    emptyMessage?: string;
    class?: string;
  }

  let {
    columns,
    rows,
    maxRows = 100,
    emptyMessage = 'No data to display',
    class: className,
  }: Props = $props();

  const displayedRows = $derived(rows.slice(0, maxRows));

  function getCellValue(row: T, key: keyof T | string): unknown {
    if (typeof key === 'string' && key.includes('.')) {
      return key.split('.').reduce((obj: unknown, k) => {
        if (obj && typeof obj === 'object') {
          return (obj as Record<string, unknown>)[k];
        }
        return undefined;
      }, row);
    }
    return row[key as keyof T];
  }
</script>

<div class={cn('overflow-auto border border-mcat-border rounded-lg', className)}>
  <table class="w-full text-sm">
    <thead class="bg-mcat-card sticky top-0">
      <tr>
        {#each columns as col}
          <th
            class="px-4 py-3 text-left font-medium text-mcat-text-label border-b border-mcat-border"
            style={col.width ? `width: ${col.width}` : undefined}
          >
            {col.header}
          </th>
        {/each}
      </tr>
    </thead>
    <tbody class="divide-y divide-mcat-border">
      {#if displayedRows.length === 0}
        <tr>
          <td
            colspan={columns.length}
            class="px-4 py-8 text-center text-mcat-text-muted"
          >
            {emptyMessage}
          </td>
        </tr>
      {:else}
        {#each displayedRows as row}
          <tr class="hover:bg-mcat-card/50 transition-colors">
            {#each columns as col}
              <td class="px-4 py-3 text-mcat-text">
                {getCellValue(row, col.key) ?? ''}
              </td>
            {/each}
          </tr>
        {/each}
      {/if}
    </tbody>
  </table>

  {#if rows.length > maxRows}
    <div class="px-4 py-2 text-xs text-mcat-text-muted bg-mcat-card border-t border-mcat-border">
      Showing {maxRows} of {rows.length} rows
    </div>
  {/if}
</div>

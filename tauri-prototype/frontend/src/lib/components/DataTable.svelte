<script lang="ts" generics="T">
  import { cn } from '$lib/utils';
  import { open } from '@tauri-apps/plugin-shell';

  interface Column<T> {
    key: keyof T | string;
    header: string;
    width?: string;
    type?: 'text' | 'link' | 'status';
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

  const statusColors: Record<string, string> = {
    live: 'text-status-live',
    removed: 'text-status-removed',
    restricted: 'text-status-restricted',
    error: 'text-status-error',
    pending: 'text-text-muted',
  };

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

  function isUrl(value: unknown): boolean {
    if (typeof value !== 'string') return false;
    return value.startsWith('http://') || value.startsWith('https://');
  }

  function getStatusColor(status: string): string {
    const normalized = status.toLowerCase();
    return statusColors[normalized] ?? 'text-text-body';
  }

  async function openLink(url: string) {
    await open(url);
  }
</script>

<div class={cn('overflow-auto border border-border-mid rounded-lg', className)}>
  <table class="min-w-full text-sm whitespace-nowrap">
    <thead class="bg-bg-controls sticky top-0">
      <tr>
        {#each columns as col}
          <th
            class="px-4 py-3 text-left font-medium text-text-primary border-b border-border-mid"
            style={col.width ? `width: ${col.width}` : undefined}
          >
            {col.header}
          </th>
        {/each}
      </tr>
    </thead>
    <tbody class="divide-y divide-border-mid">
      {#if displayedRows.length === 0}
        <tr>
          <td
            colspan={columns.length}
            class="px-4 py-8 text-center text-text-muted"
          >
            {emptyMessage}
          </td>
        </tr>
      {:else}
        {#each displayedRows as row}
          <tr class="hover:bg-bg-controls/50 transition-colors">
            {#each columns as col}
              {@const value = getCellValue(row, col.key)}
              <td class="px-4 py-3 text-text-body">
                {#if (col.type === 'link' || col.key === 'url') && isUrl(value)}
                  <button
                    type="button"
                    class="text-accent-brown text-left truncate max-w-[280px] block cursor-pointer"
                    onclick={() => openLink(String(value))}
                    title={String(value)}
                  >
                    {value}
                  </button>
                {:else if col.type === 'status' || col.key === 'status'}
                  <span class={cn('font-medium', getStatusColor(String(value ?? '')))}>
                    {value ?? ''}
                  </span>
                {:else}
                  {value ?? ''}
                {/if}
              </td>
            {/each}
          </tr>
        {/each}
      {/if}
    </tbody>
  </table>

  {#if rows.length > maxRows}
    <div class="px-4 py-2 text-xs text-text-muted bg-bg-controls border-t border-border-mid">
      Showing {maxRows} of {rows.length} rows
    </div>
  {/if}
</div>

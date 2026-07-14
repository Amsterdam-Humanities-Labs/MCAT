<script lang="ts" generics="T">
  import { cn } from '$lib/utils';
  import TransitionBadge from './TransitionBadge.svelte';
  import StatusBadge from './StatusBadge.svelte';
  import { Link } from '@mcat/ui';

  interface Column<T> {
    key: keyof T | string;
    header: string;
    width?: string;
    type?: 'text' | 'link' | 'status' | 'transition' | 'file';
  }

  interface Props {
    columns: Column<T>[];
    rows: T[];
    maxRows?: number;
    emptyMessage?: string;
    onScreenshotClick?: (path: string) => void;
    class?: string;
  }

  let {
    columns,
    rows,
    maxRows = 100,
    emptyMessage = 'No data to display',
    onScreenshotClick,
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

  function isUrl(value: unknown): boolean {
    if (typeof value !== 'string') return false;
    return value.startsWith('http://') || value.startsWith('https://');
  }


</script>

<div class={cn('overflow-auto border border-border-mid rounded', className)}>
  <table class="min-w-full text-base whitespace-nowrap">
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
            class="px-4 py-8 text-center text-text-secondary"
          >
            {emptyMessage}
          </td>
        </tr>
      {:else}
        {#each displayedRows as row}
          <tr class="hover:bg-interactive-row transition-colors">
            {#each columns as col}
              {@const value = getCellValue(row, col.key)}
              <td class="px-4 py-3 text-text-body">
                {#if (col.type === 'link' || col.key === 'url') && isUrl(value)}
                  <Link href={String(value)} class="block truncate">{value}</Link>
                {:else if col.type === 'file' && value && onScreenshotClick}
                  <button
                    class="text-accent-primary underline decoration-accent-primary/40 hover:decoration-accent-primary cursor-pointer truncate max-w-[200px] block text-left"
                    onclick={() => onScreenshotClick(String(value))}
                  >
                    {String(value).split('/').pop()}
                  </button>
                {:else if col.type === 'file'}
                  <span class="text-text-secondary">{value ? String(value).split('/').pop() : ''}</span>
                {:else if col.type === 'transition'}
                  {@const prev = String(getCellValue(row, 'previous_status') ?? '')}
                  {@const curr = String(getCellValue(row, 'mcat_status') ?? '')}
                  <TransitionBadge from={prev} to={curr} />
                {:else if col.type === 'status' || col.key === 'mcat_status'}
                  <StatusBadge status={String(value ?? '').toLowerCase()} />
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
    <div class="px-4 py-2 text-base text-text-secondary bg-bg-controls border-t border-border-mid">
      Showing {maxRows} of {rows.length} rows
    </div>
  {/if}
</div>

<script lang="ts" generics="T">
  import { cn } from '$lib/utils';
  import { Image } from 'phosphor-svelte';
  import TransitionBadge from './TransitionBadge.svelte';
  import StatusBadge from './StatusBadge.svelte';
  import Link from './Link.svelte';

  interface Column<T> {
    key: keyof T | string;
    header: string;
    width?: string;
    type?: 'text' | 'link' | 'status' | 'transition';
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
                  <div class="flex items-center gap-2">
                    {#if onScreenshotClick}
                      {@const screenshotPath = String(getCellValue(row, 'screenshot_path') ?? '')}
                      {#if screenshotPath}
                        <button
                          class="shrink-0 cursor-pointer opacity-60 hover:opacity-100 text-text-secondary"
                          onclick={() => onScreenshotClick(screenshotPath)}
                          title="Open screenshot"
                        >
                          <Image size={16} />
                        </button>
                      {/if}
                    {/if}
                    <Link href={String(value)} class="max-w-[280px] block">{value}</Link>
                  </div>
                {:else if col.type === 'transition'}
                  {@const prev = String(getCellValue(row, 'previous_status') ?? '')}
                  {@const curr = String(getCellValue(row, 'status') ?? '')}
                  <TransitionBadge from={prev} to={curr} />
                {:else if col.type === 'status' || col.key === 'status'}
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

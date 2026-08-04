<script lang="ts">
  import { cn } from './utils';
  import { statusLabel, statusBadge } from './status';

  interface Props {
    status: string;
    count?: number;
    /** 'lg' — full labeled pill; 'sm' — a tiny label-less swatch for legends. */
    size?: 'sm' | 'lg';
    class?: string;
  }

  let { status, count, size = 'lg', class: className }: Props = $props();

  // Both sizes pull the same badge colors, so the pill and its legend swatch stay in sync.
  const classes = $derived(statusBadge(status));
</script>

{#if size === 'sm'}
  <span class={cn('inline-block h-2.5 w-4 rounded-sm border', classes, className)} aria-hidden="true"></span>
{:else}
  <span
    class={cn(
      'inline-flex items-center px-2 py-0.5 text-base rounded-pill border whitespace-nowrap',
      classes,
      className,
    )}
  >
    {statusLabel(status)}{#if count !== undefined} ({count}){/if}
  </span>
{/if}

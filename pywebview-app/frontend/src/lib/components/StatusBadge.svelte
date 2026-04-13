<script lang="ts">
  import { cn } from '$lib/utils';

  interface Props {
    status: string;
    count?: number;
    class?: string;
  }

  let { status, count, class: className }: Props = $props();

  const statusConfig: Record<string, { label: string; classes: string }> = {
    live: {
      label: 'Live',
      classes: 'bg-badge-live-bg text-status-live border-badge-live-border',
    },
    removed: {
      label: 'Removed',
      classes: 'bg-badge-removed-bg text-status-removed border-badge-removed-border',
    },
    restricted: {
      label: 'Restricted',
      classes: 'bg-badge-restricted-bg text-status-restricted border-badge-restricted-border',
    },
    private: {
      label: 'Private',
      classes: 'bg-badge-restricted-bg text-status-restricted border-badge-restricted-border',
    },
    error: {
      label: 'Error',
      classes: 'bg-badge-error-bg text-status-error border-badge-error-border',
    },
  };

  const normalized = $derived(status.toLowerCase());
  const config = $derived(statusConfig[normalized] ?? { label: status, classes: 'bg-bg-controls text-text-secondary border-border-light' });
</script>

<span
  class={cn(
    'inline-flex items-center px-2 py-0.5 text-base rounded border whitespace-nowrap',
    config.classes,
    className
  )}
>
  {config.label}{#if count !== undefined} ({count}){/if}
</span>

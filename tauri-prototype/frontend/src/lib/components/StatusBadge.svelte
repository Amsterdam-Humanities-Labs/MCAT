<script lang="ts">
  import { cn } from '$lib/utils';
  import type { ContentStatus } from '$types/processing';

  interface Props {
    status: ContentStatus;
    class?: string;
  }

  let { status, class: className }: Props = $props();

  const statusConfig: Record<ContentStatus, { label: string; classes: string }> = {
    live: {
      label: 'Live',
      classes: 'bg-status-live/20 text-status-live border-status-live/30',
    },
    removed: {
      label: 'Removed',
      classes: 'bg-status-removed/20 text-status-removed border-status-removed/30',
    },
    restricted: {
      label: 'Restricted',
      classes: 'bg-status-restricted/20 text-status-restricted border-status-restricted/30',
    },
    error: {
      label: 'Error',
      classes: 'bg-status-error/20 text-status-error border-status-error/30',
    },
    pending: {
      label: 'Pending',
      classes: 'bg-status-pending/20 text-status-pending border-status-pending/30',
    },
  };

  const config = $derived(statusConfig[status] ?? statusConfig.pending);
</script>

<span
  class={cn(
    'inline-flex items-center px-2 py-0.5 text-xs font-medium rounded border',
    config.classes,
    className
  )}
>
  {config.label}
</span>

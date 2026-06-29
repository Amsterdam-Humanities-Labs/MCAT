<script lang="ts">
  import { cn } from '$lib/utils';

  interface Props {
    status: string;
    count?: number;
    class?: string;
  }

  let { status, count, class: className }: Props = $props();

  const restrictedClasses = 'bg-badge-restricted-bg text-status-restricted border-badge-restricted-border';
  const unavailableClasses = 'bg-badge-unavailable-bg text-status-unavailable border-badge-unavailable-border';

  const statusConfig: Record<string, { label: string; classes: string }> = {
    live: {
      label: 'Live',
      classes: 'bg-badge-live-bg text-status-live border-badge-live-border',
    },
    unavailable: {
      label: 'Unavailable',
      classes: unavailableClasses,
    },
    moderated: {
      label: 'Moderated',
      classes: 'bg-badge-moderated-bg text-status-moderated border-badge-moderated-border',
    },
    restricted: {
      label: 'Restricted',
      classes: restrictedClasses,
    },
    'login required': {
      label: 'Login Required',
      classes: 'bg-badge-login-bg text-status-login border-badge-login-border',
    },
    error: {
      label: 'Error',
      classes: 'bg-badge-error-bg text-status-error border-badge-error-border',
    },
    unknown: {
      label: 'Unknown',
      classes: 'bg-badge-unknown-bg text-status-unknown border-badge-unknown-border',
    },
    // Legacy statuses retained for results recorded before the taxonomy change.
    removed: { label: 'Removed', classes: unavailableClasses },
    private: { label: 'Private', classes: restrictedClasses },
    'age-restricted': { label: 'Age-restricted', classes: restrictedClasses },
    'geo-blocked': { label: 'Geo-blocked', classes: restrictedClasses },
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

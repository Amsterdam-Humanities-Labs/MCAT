<script lang="ts">
  import { cn } from '$lib/utils';

  interface Props {
    from: string;
    to: string;
    count?: number;
    class?: string;
  }

  let { from, to, count, class: className }: Props = $props();

  function statusLabel(s: string): string {
    const map: Record<string, string> = { live: 'Live', removed: 'Removed', restricted: 'Restricted', error: 'Error', private: 'Private' };
    return map[s.toLowerCase()] || s.charAt(0).toUpperCase() + s.slice(1);
  }

  function badgeClasses(status: string): string {
    switch (status.toLowerCase()) {
      case 'live': return 'text-status-live bg-badge-live-bg border-badge-live-border';
      case 'removed': return 'text-status-removed bg-badge-removed-bg border-badge-removed-border';
      case 'restricted': case 'private': return 'text-status-restricted bg-badge-restricted-bg border-badge-restricted-border';
      case 'error': return 'text-status-error bg-badge-error-bg border-badge-error-border';
      default: return 'text-text-secondary bg-bg-controls border-border-light';
    }
  }
</script>

<span class={cn("inline-block px-2 py-0.5 rounded text-base border whitespace-nowrap", badgeClasses(to), className)}>
  {statusLabel(from)} → {statusLabel(to)}{#if count !== undefined} ({count}){/if}
</span>

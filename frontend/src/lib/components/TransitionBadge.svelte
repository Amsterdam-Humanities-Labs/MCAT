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
    const map: Record<string, string> = {
      live: 'Live', unavailable: 'Unavailable', moderated: 'Moderated',
      restricted: 'Restricted', 'login required': 'Login Required', unknown: 'Unknown',
      error: 'Error', removed: 'Removed', private: 'Private',
    };
    return map[s.toLowerCase()] || s.charAt(0).toUpperCase() + s.slice(1);
  }

  function badgeClasses(status: string): string {
    switch (status.toLowerCase()) {
      case 'live': return 'text-status-live bg-badge-live-bg border-badge-live-border';
      case 'unavailable': case 'removed': return 'text-status-unavailable bg-badge-unavailable-bg border-badge-unavailable-border';
      case 'moderated': return 'text-status-moderated bg-badge-moderated-bg border-badge-moderated-border';
      case 'restricted': case 'private': case 'age-restricted': case 'geo-blocked': return 'text-status-restricted bg-badge-restricted-bg border-badge-restricted-border';
      case 'login required': return 'text-status-login bg-badge-login-bg border-badge-login-border';
      case 'error': return 'text-status-error bg-badge-error-bg border-badge-error-border';
      case 'unknown': return 'text-status-unknown bg-badge-unknown-bg border-badge-unknown-border';
      default: return 'text-text-secondary bg-bg-controls border-border-light';
    }
  }
</script>

<span class={cn("inline-block px-2 py-0.5 rounded text-base border whitespace-nowrap", badgeClasses(to), className)}>
  {statusLabel(from)} → {statusLabel(to)}{#if count !== undefined} ({count}){/if}
</span>

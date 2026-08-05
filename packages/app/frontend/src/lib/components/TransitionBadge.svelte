<script lang="ts">
  import { cn } from '$lib/utils';
  import { statusLabel, statusBadge } from '@mcat/shared-ui';

  interface Props {
    from: string;
    to: string;
    count?: number;
    class?: string;
  }

  let { from, to, count, class: className }: Props = $props();
</script>

<span class={cn("inline-block px-2 py-0.5 rounded text-base border whitespace-nowrap", statusBadge(to), className)}>
  {statusLabel(from)} → {statusLabel(to)}{#if count !== undefined} ({count}){/if}
</span>

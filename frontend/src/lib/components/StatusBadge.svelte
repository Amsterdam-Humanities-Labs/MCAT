<script lang="ts">
  import { cn } from '$lib/utils';
  import { statusLabel, statusBadge } from '$lib/status';

  interface Props {
    status: string;
    count?: number;
    class?: string;
  }

  let { status, count, class: className }: Props = $props();

  const config = $derived({ label: statusLabel(status), classes: statusBadge(status) });
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

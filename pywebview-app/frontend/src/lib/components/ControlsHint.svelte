<script lang="ts">
  import { cn } from '$lib/utils';
  import { formatDuration } from '$lib/utils/format';

  interface Props {
    durationSeconds: number | null;
    class?: string;
  }

  let { durationSeconds, class: className }: Props = $props();

  const text = $derived(
    durationSeconds ? `Last run took ${formatDuration(durationSeconds)}` : ''
  );
</script>

{#if text}
  <span class={cn("text-text-hint", className)}>{text}</span>
{/if}

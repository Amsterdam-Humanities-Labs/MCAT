<script lang="ts">
  import { cn } from '$lib/utils';
  import { formatTimestamp } from '$lib/utils/format';
  import { HourglassIcon, StopIcon } from 'phosphor-svelte';

  interface Props {
    timestamp: string;
    paused?: boolean;
    class?: string;
  }

  let { timestamp, paused = false, class: className }: Props = $props();
</script>

<div
  class={cn("flex items-center gap-3 px-4 py-2.5 text-base border-b border-border-light", className)}
  class:runrow-pulse={!paused}
>
  <span class="inline-flex items-center justify-center w-5 h-5 shrink-0">
    {#if paused}
      <StopIcon size={16} class="text-timeline-dot" />
    {:else}
      <HourglassIcon size={16} class="text-timeline-dot" />
    {/if}
  </span>
  <span class="flex items-center gap-2">
    <span class="text-text-secondary">{formatTimestamp(timestamp)}</span>
    {#if paused}
      <span class="text-text-primary">Paused</span>
    {:else}
      <span class="text-text-primary">Running</span>
    {/if}
  </span>
</div>

<style>
  /* Active (running) row: slow background pulse from the timeline tint toward
     the lighter primary and back, to signal a live run. */
  .runrow-pulse {
    animation: runrow-pulse 3s ease-in-out infinite;
  }
  @keyframes runrow-pulse {
    0%, 100% { background-color: var(--color-bg-timeline); }
    50% { background-color: var(--color-bg-primary); }
  }
</style>

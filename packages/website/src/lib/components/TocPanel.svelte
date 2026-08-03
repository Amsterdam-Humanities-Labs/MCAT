<script lang="ts">
  import type { Snippet } from 'svelte';
  import { cn } from '@mcat/shared-ui';
  import TocToggle from './TocToggle.svelte';

  interface Props {
    expanded?: boolean;
    topOffset?: number;
    children: Snippet;
  }

  let { expanded = $bindable(true), topOffset = 56, children }: Props = $props();

  function handleKeydown(event: KeyboardEvent) {
    if (event.key === 'Escape') expanded = false;
  }
</script>

<svelte:window onkeydown={handleKeydown} />

<div
  class={cn(
    'fixed left-0 z-30 w-72 border-r border-border-light bg-bg-primary shadow-[5px_0_20px_5px_rgba(0,0,0,0.07)] transition-transform duration-200 ease-out',
    expanded ? 'translate-x-0' : '-translate-x-full',
  )}
  style="top: {topOffset}px; height: calc(100dvh - {topOffset}px);"
>
  <TocToggle
    {expanded}
    onclick={() => (expanded = !expanded)}
    class="absolute right-[-30px] top-1/2 -translate-y-1/2"
  />

  <div class="h-full overflow-y-auto px-4 pb-6 pt-4" inert={!expanded}>
    {@render children()}
  </div>
</div>

<script lang="ts">
  import { cn } from '$lib/utils';
  import type { LogMessage } from '$types/console';
  import ConsoleEntry from './ConsoleEntry.svelte';

  interface Props {
    entries: LogMessage[];
    class?: string;
  }

  let { entries, class: className }: Props = $props();

  let containerEl: HTMLDivElement | undefined = $state();
  let autoScroll = $state(true);

  function handleScroll() {
    if (!containerEl) return;
    const { scrollTop, scrollHeight, clientHeight } = containerEl;
    autoScroll = scrollHeight - scrollTop - clientHeight < 50;
  }

  $effect(() => {
    if (autoScroll && containerEl && entries.length > 0) {
      containerEl.scrollTop = containerEl.scrollHeight;
    }
  });
</script>

<div
  bind:this={containerEl}
  onscroll={handleScroll}
  class={cn("overflow-auto p-3 bg-bg-timeline flex-1", className)}
  style="max-height: 300px"
>
  {#if entries.length === 0}
    <div class="text-text-secondary italic">No messages yet...</div>
  {:else}
    {#each entries as msg (msg.id)}
      <ConsoleEntry
        timestamp={msg.timestamp}
        message={msg.text}
        level={msg.level}
      />
    {/each}
  {/if}
</div>

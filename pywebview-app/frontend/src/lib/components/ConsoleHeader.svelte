<script lang="ts">
  import { cn } from '$lib/utils';
  import { CaretUp, CaretDown } from 'phosphor-svelte';

  interface Props {
    expanded: boolean;
    warningCount: number;
    onToggle?: () => void;
    class?: string;
  }

  let { expanded, warningCount, onToggle, class: className }: Props = $props();
</script>

<button
  class={cn("h-9 px-4 flex items-center gap-3 bg-bg-controls border-t border-border-mid w-full cursor-ns-resize hover:bg-bg-toolbar transition-colors", className)}
  onclick={onToggle}
>
  <span class="font-bold text-text-primary">Console</span>
  {#if warningCount > 0}
    <span class="text-console-warning-count font-semibold">{warningCount} warnings</span>
  {/if}
  <span class="ml-auto text-text-secondary">
    {#if expanded}
      <CaretDown size={16} />
    {:else}
      <CaretUp size={16} />
    {/if}
  </span>
</button>

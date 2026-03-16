<script lang="ts">
  import { CaretUp, CaretDown } from 'phosphor-svelte';

  interface Props {
    expanded: boolean;
    warningCount: number;
    onToggle?: () => void;
  }

  let { expanded, warningCount, onToggle }: Props = $props();
</script>

<button
  class="h-9 px-4 flex items-center gap-3 bg-bg-controls border-t border-border-mid w-full cursor-pointer hover:bg-bg-toolbar transition-colors"
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

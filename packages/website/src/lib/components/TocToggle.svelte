<script lang="ts">
  import { cn } from '@mcat/shared-ui';
  import { CaretLeft, List } from 'phosphor-svelte';

  interface Props {
    expanded: boolean;
    onclick: () => void;
    class?: string;
  }

  let { expanded, onclick, class: className }: Props = $props();
</script>

<button
  {onclick}
  class={cn(
    'flex h-[45px] w-[30px] items-center justify-center rounded-r-full border border-l-0 border-border-light bg-bg-primary pr-1 text-text-secondary hover:bg-interactive-hover',
    className,
  )}
  aria-label={expanded ? 'Collapse contents' : 'Expand contents'}
  aria-expanded={expanded}
>
  {#if expanded}
    <CaretLeft size={18} weight="bold" />
  {:else}
    <List size={18} weight="bold" />
  {/if}
</button>

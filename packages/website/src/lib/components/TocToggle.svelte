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
    'flex h-[30px] w-[30px] items-center justify-center rounded-r-pill border border-border-light bg-bg-toolbar text-text-secondary hover:bg-accent-primary hover:text-chrome-text',
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

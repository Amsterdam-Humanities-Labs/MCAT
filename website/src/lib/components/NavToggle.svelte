<script lang="ts">
  import { List, X } from 'phosphor-svelte';
  import { cn } from '@mcat/shared-ui';

  interface Props {
    open: boolean;
    onclick: () => void;
    class?: string;
  }

  let { open, onclick, class: className }: Props = $props();
</script>

<button
  type="button"
  class={cn('p-2 text-text-primary', className)}
  aria-label={open ? 'Close navigation menu' : 'Open navigation menu'}
  aria-expanded={open}
  {onclick}
>
  {#if open}
    <X weight="bold" size={24} />
  {:else}
    <List weight="bold" size={24} />
  {/if}
</button>

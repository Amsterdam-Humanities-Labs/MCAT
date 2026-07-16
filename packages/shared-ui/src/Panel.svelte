<script lang="ts">
  import type { Snippet } from 'svelte';
  import { cn } from './utils';

  interface Props {
    title?: string;
    class?: string;
    bodyClass?: string;
    actions?: Snippet;
    children?: Snippet;
  }

  let { title, class: className, bodyClass, actions, children }: Props = $props();
</script>

<section class={cn('overflow-hidden rounded border border-border-light bg-bg-detail', className)}>
  {#if title || actions}
    <header
      class="flex items-center justify-between gap-3 border-b border-border-light bg-bg-toolbar px-3 py-2 text-base text-text-secondary"
    >
      {#if title}<span>{title}</span>{/if}
      {@render actions?.()}
    </header>
  {/if}
  <div class={cn('p-3', bodyClass)}>
    {@render children?.()}
  </div>
</section>

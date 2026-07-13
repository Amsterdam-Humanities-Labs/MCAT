<script lang="ts">
  import { cn } from './utils';

  interface Props {
    href: string;
    class?: string;
    children?: import('svelte').Snippet;
  }

  let { href, class: className, children }: Props = $props();
</script>

<a
  {href}
  target="_blank"
  rel="noopener"
  class={cn("text-accent-primary underline decoration-accent-primary/40 hover:decoration-accent-primary truncate", className)}
>
  {#if children}
    {@render children()}
  {:else}
    {href}
  {/if}
</a>

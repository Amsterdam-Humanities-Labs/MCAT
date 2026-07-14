<script lang="ts">
  import type { Snippet } from 'svelte';
  import type { HTMLAnchorAttributes } from 'svelte/elements';
  import { cn } from './utils';

  interface Props extends HTMLAnchorAttributes {
    href: string;
    class?: string;
    children?: Snippet;
  }

  let { href, class: className, children, ...rest }: Props = $props();

  // Only external links open a new tab; internal (/…) links stay in-app for SvelteKit routing.
  const external = $derived(/^(https?:)?\/\//.test(href));
</script>

<a
  {...rest}
  {href}
  target={external ? '_blank' : undefined}
  rel={external ? 'noopener' : undefined}
  class={cn("text-accent-primary underline decoration-accent-primary/40 hover:decoration-accent-primary", className)}
>
  {#if children}
    {@render children()}
  {:else}
    {href}
  {/if}
</a>

<script lang="ts">
  import type { Snippet } from 'svelte';
  import { cn } from '@mcat/shared-ui';

  interface Props {
    href: string;
    depth: number;
    active: boolean;
    children: Snippet;
  }

  let { href, depth, active, children }: Props = $props();
</script>

<li>
  <a
    {href}
    class={cn(
      'block py-1 text-text-secondary hover:text-text-primary',
      depth === 3 && 'pl-4',
      active && 'text-text-primary underline underline-offset-4',
    )}
  >
    {@render children()}
  </a>
</li>

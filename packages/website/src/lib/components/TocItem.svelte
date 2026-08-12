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
      'inline-block border-b-4 border-transparent pb-[2.5px] text-lg text-text-secondary hover:border-accent-primary hover:text-text-primary',
      depth === 3 && 'ml-4',
      active && 'border-accent-primary text-text-primary',
    )}
  >
    {@render children()}
  </a>
</li>

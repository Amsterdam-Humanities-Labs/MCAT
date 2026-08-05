<script lang="ts">
  import type { Snippet } from 'svelte';
  import type { HTMLAttributes } from 'svelte/elements';
  import { cn } from '@mcat/shared-ui';

  interface Props extends HTMLAttributes<HTMLHeadingElement> {
    class?: string;
    children?: Snippet;
  }

  let { class: className, children, ...rest }: Props = $props();
</script>

<h3 {...rest} class={cn('text-xl font-medium text-text-primary md:text-2xl', className)}>
  {@render children?.()}
</h3>

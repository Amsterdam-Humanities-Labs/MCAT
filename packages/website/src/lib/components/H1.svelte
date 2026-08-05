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

<h1 {...rest} class={cn('text-3xl font-medium text-text-primary md:text-5xl', className)}>
  {@render children?.()}
</h1>

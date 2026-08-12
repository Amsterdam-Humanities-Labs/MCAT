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

<h5 {...rest} class={cn('text-base font-bold text-text-primary md:text-lg', className)}>
  {@render children?.()}
</h5>

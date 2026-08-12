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

<h4 {...rest} class={cn('text-lg font-bold text-text-primary md:text-xl', className)}>
  {@render children?.()}
</h4>

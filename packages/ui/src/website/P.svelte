<script lang="ts">
  import type { Snippet } from 'svelte';
  import type { HTMLAttributes } from 'svelte/elements';
  import { cn } from '../utils';

  interface Props extends HTMLAttributes<HTMLParagraphElement> {
    class?: string;
    children?: Snippet;
  }

  let { class: className, children, ...rest }: Props = $props();
</script>

<p {...rest} class={cn('text-base leading-relaxed text-text-body', className)}>
  {@render children?.()}
</p>

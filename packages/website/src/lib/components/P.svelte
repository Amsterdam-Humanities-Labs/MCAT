<script lang="ts">
  import type { Snippet } from 'svelte';
  import type { HTMLAttributes } from 'svelte/elements';
  import { cn } from '@mcat/shared-ui';

  interface Props extends HTMLAttributes<HTMLParagraphElement> {
    variant?: 'body' | 'warning';
    class?: string;
    children?: Snippet;
  }

  let { variant = 'body', class: className, children, ...rest }: Props = $props();

  const variantClasses = {
    body: 'text-text-body',
    warning: 'font-medium text-status-removed',
  };
</script>

<p {...rest} class={cn('text-base leading-relaxed', variantClasses[variant], className)}>
  {@render children?.()}
</p>

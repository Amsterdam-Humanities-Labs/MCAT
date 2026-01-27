<script lang="ts">
  import { cn } from '$lib/utils';

  interface Props {
    variant?: 'default' | 'success' | 'error' | 'warning' | 'info';
    size?: 'sm' | 'md';
    class?: string;
    children?: import('svelte').Snippet;
  }

  let {
    variant = 'default',
    size = 'md',
    class: className,
    children,
  }: Props = $props();

  const baseClasses = 'inline-flex items-center font-medium rounded-full';

  const variants = {
    default: 'bg-mcat-border text-mcat-text',
    success: 'bg-mcat-success-bg text-mcat-success',
    error: 'bg-mcat-error-bg text-mcat-error',
    warning: 'bg-amber-900/50 text-amber-400',
    info: 'bg-blue-900/50 text-blue-400',
  };

  const sizes = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-1 text-sm',
  };
</script>

<span class={cn(baseClasses, variants[variant], sizes[size], className)}>
  {@render children?.()}
</span>

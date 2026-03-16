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
    default: 'bg-border-mid text-text-body',
    success: 'bg-status-live/10 text-status-live',
    error: 'bg-status-removed/10 text-status-removed',
    warning: 'bg-status-restricted/10 text-status-restricted',
    info: 'bg-link-blue/10 text-link-blue',
  };

  const sizes = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-1 text-sm',
  };
</script>

<span class={cn(baseClasses, variants[variant], sizes[size], className)}>
  {@render children?.()}
</span>

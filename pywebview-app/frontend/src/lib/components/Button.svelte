<script lang="ts">
  import { cn } from '$lib/utils';
  import { SpinnerGap } from 'phosphor-svelte';

  interface Props {
    variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
    size?: 'sm' | 'md' | 'lg';
    disabled?: boolean;
    loading?: boolean;
    type?: 'button' | 'submit' | 'reset';
    class?: string;
    onclick?: (e: MouseEvent) => void;
    children?: import('svelte').Snippet;
  }

  let {
    variant = 'secondary',
    size = 'md',
    disabled = false,
    loading = false,
    type = 'button',
    class: className,
    onclick,
    children,
  }: Props = $props();

  const baseClasses =
    'inline-flex items-center justify-center font-medium rounded transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-bg-primary disabled:opacity-50 disabled:cursor-not-allowed';

  const variants = {
    primary:
      'bg-accent-brown hover:bg-accent-brown/90 text-white focus:ring-accent-brown',
    secondary:
      'bg-transparent hover:bg-accent-brown/10 text-accent-brown border border-accent-brown focus:ring-accent-brown',
    danger:
      'bg-transparent hover:bg-status-removed/10 text-status-removed border border-status-removed focus:ring-status-removed',
    ghost:
      'bg-transparent hover:bg-bg-controls text-text-body focus:ring-border-mid',
  };

  const sizes = {
    sm: 'px-3 py-2 text-sm',
    md: 'px-4 py-2 text-sm',
    lg: 'px-6 py-3 text-base',
  };
</script>

<button
  {type}
  disabled={disabled || loading}
  class={cn(baseClasses, variants[variant], sizes[size], className)}
  onclick={onclick}
>
  {#if loading}
    <SpinnerGap size={16} class="animate-spin -ml-1 mr-2" />
  {/if}
  {@render children?.()}
</button>

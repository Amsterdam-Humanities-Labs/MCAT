<script lang="ts">
  import { cn } from './utils';
  import { SpinnerGap } from 'phosphor-svelte';

  interface Props {
    href?: string;
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
    href,
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
    'inline-flex items-center justify-center font-medium rounded transition-colors cursor-pointer focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-bg-primary disabled:opacity-50 disabled:cursor-not-allowed';

  const variants = {
    primary:
      'bg-accent-primary hover:bg-accent-primary-hover text-white focus:ring-accent-primary',
    secondary:
      'bg-bg-toolbar hover:bg-accent-primary/10 text-accent-primary border border-accent-primary focus:ring-accent-primary',
    danger:
      'bg-bg-toolbar hover:bg-interactive-danger text-status-removed border border-status-removed focus:ring-status-removed',
    ghost:
      'bg-transparent hover:bg-interactive-hover text-text-body focus:ring-border-mid',
  };

  const sizes = {
    sm: 'px-3 py-2 text-base',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-base',
  };

  const classes = $derived(cn(baseClasses, variants[variant], sizes[size], className));

  // Cross-origin links open in a new tab; internal ones use client-side nav.
  const external = $derived(href ? /^(https?:)?\/\//.test(href) : false);
</script>

{#if href}
  <a
    {href}
    target={external ? '_blank' : undefined}
    rel={external ? 'noopener' : undefined}
    class={classes}
    {onclick}
  >
    {#if loading}
      <SpinnerGap size={16} class="animate-spin -ml-1 mr-2" />
    {/if}
    {@render children?.()}
  </a>
{:else}
  <button {type} disabled={disabled || loading} class={classes} {onclick}>
    {#if loading}
      <SpinnerGap size={16} class="animate-spin -ml-1 mr-2" />
    {/if}
    {@render children?.()}
  </button>
{/if}

<script lang="ts">
  import { cn } from './utils';

  interface Props {
    href?: string;
    variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
    size?: 'sm' | 'md' | 'lg';
    disabled?: boolean;
    loading?: boolean;
    type?: 'button' | 'submit' | 'reset';
    class?: string;
    // Return value is only inspected for thenable-ness, never consumed.
    onclick?: (e: MouseEvent) => unknown;
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

  // A handler that returns a promise disables the button until it settles, so
  // async work cannot be fired twice by a second click. Handlers returning void
  // are unaffected.
  let pending = $state(false);
  const busy = $derived(loading || pending);

  // Endpoints of the busy pulse: the variant's own background, and its
  // pulse token from the theme.
  const pulseEnds = {
    primary: ['var(--color-accent-primary)', 'var(--color-btn-pulse-primary)'],
    secondary: ['var(--color-bg-toolbar)', 'var(--color-btn-pulse-secondary)'],
    danger: ['var(--color-bg-toolbar)', 'var(--color-btn-pulse-danger)'],
    ghost: ['transparent', 'var(--color-btn-pulse-ghost)'],
  };

  const pulseStyle = $derived(
    busy ? `--btn-base:${pulseEnds[variant][0]};--btn-pulse:${pulseEnds[variant][1]}` : undefined,
  );

  const classes = $derived(
    cn(
      baseClasses,
      variants[variant],
      sizes[size],
      // While busy the pulse carries the state, so skip the disabled dimming
      // that would otherwise wash it out.
      busy && 'disabled:opacity-100 btn-pulse',
      className,
    ),
  );

  async function handleClick(e: MouseEvent) {
    if (pending) return;
    const result = onclick?.(e);
    if (typeof (result as { then?: unknown } | undefined)?.then !== 'function') return;
    pending = true;
    try {
      await result;
    } finally {
      pending = false;
    }
  }

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
    {@render children?.()}
  </a>
{:else}
  <button
    {type}
    disabled={disabled || busy}
    class={classes}
    style={pulseStyle}
    onclick={handleClick}
  >
    <!-- Only the label dims while busy; dimming the whole button would flatten
         the pulse it sits on. -->
    <span class={busy ? 'opacity-50' : undefined}>
      {@render children?.()}
    </span>
  </button>
{/if}

<style>
  /* Busy state: the same slow background breathe as the running timeline row,
     between the variant's own background and its pulse colour. */
  :global(.btn-pulse) {
    animation: btn-pulse 3s ease-in-out infinite;
  }
  @keyframes btn-pulse {
    0%, 100% { background-color: var(--btn-base); }
    50% { background-color: var(--btn-pulse); }
  }
</style>

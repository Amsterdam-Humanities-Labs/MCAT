<script lang="ts">
  import type { Component } from 'svelte';
  import { cn } from './utils';

  type IconWeight = 'thin' | 'light' | 'regular' | 'bold' | 'fill' | 'duotone';
  // A phosphor-svelte icon component (e.g. `X`, `XIcon`). Structural type so any
  // phosphor icon assigns; phosphor's own props are a superset of these.
  type PhosphorIcon = Component<{
    size?: number | string;
    weight?: IconWeight;
    color?: string;
    mirrored?: boolean;
    class?: string;
  }>;

  interface Props {
    /** The phosphor icon to render. */
    icon: PhosphorIcon;
    /** Accessible name — required since the button shows no text. */
    label: string;
    variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
    size?: 'sm' | 'md' | 'lg';
    iconSize?: number;
    disabled?: boolean;
    type?: 'button' | 'submit' | 'reset';
    class?: string;
    onclick?: (e: MouseEvent) => void;
  }

  let {
    icon: Icon,
    label,
    variant = 'secondary',
    size = 'md',
    iconSize = 18,
    disabled = false,
    type = 'button',
    class: className,
    onclick,
  }: Props = $props();

  // Base + variants are copied verbatim from Button.svelte so a ButtonIcon is
  // visually identical to a text Button of the same variant.
  const baseClasses =
    'inline-flex items-center justify-center font-medium rounded transition-colors cursor-pointer focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-bg-primary disabled:opacity-50 disabled:cursor-not-allowed';

  const variants = {
    primary:
      'bg-accent-primary hover:bg-interactive-primary text-white focus:ring-accent-primary',
    secondary:
      'bg-bg-detail hover:bg-interactive-input text-accent-primary border border-accent-primary focus:ring-accent-primary',
    danger:
      'bg-transparent hover:bg-interactive-danger text-status-removed border border-status-removed focus:ring-status-removed',
    ghost:
      'bg-transparent hover:bg-interactive-hover text-text-body focus:ring-border-mid',
  };

  // Same vertical padding as Button's sizes; the h-6 (24px) content box equals
  // the text-base line-height at the app's 16px root, so the square button is
  // exactly as tall as a text Button of the same size.
  const sizes = { sm: 'p-2', md: 'p-2', lg: 'p-3' };
</script>

<button
  {type}
  {disabled}
  aria-label={label}
  class={cn(baseClasses, variants[variant], sizes[size], className)}
  onclick={onclick}
>
  <span class="flex h-6 w-6 items-center justify-center">
    <Icon size={iconSize} />
  </span>
</button>

<script lang="ts">
  import { cn } from '$lib/utils';

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
    'inline-flex items-center justify-center font-medium rounded transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-mcat-bg disabled:opacity-50 disabled:cursor-not-allowed';

  const variants = {
    primary:
      'bg-mcat-orange hover:bg-mcat-orange-dark text-white focus:ring-mcat-orange',
    secondary:
      'bg-mcat-card hover:bg-mcat-border text-mcat-text border border-mcat-border focus:ring-mcat-border',
    danger:
      'bg-mcat-danger hover:bg-mcat-danger-hover text-white focus:ring-mcat-danger',
    ghost:
      'bg-transparent hover:bg-mcat-card text-mcat-text focus:ring-mcat-border',
  };

  const sizes = {
    sm: 'px-2 py-1 text-sm',
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
    <svg
      class="animate-spin -ml-1 mr-2 h-4 w-4"
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
    >
      <circle
        class="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        stroke-width="4"
      ></circle>
      <path
        class="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      ></path>
    </svg>
  {/if}
  {@render children?.()}
</button>

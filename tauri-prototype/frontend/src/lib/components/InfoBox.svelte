<script lang="ts">
  import { cn } from '$lib/utils';

  interface Props {
    variant?: 'info' | 'warning' | 'success' | 'error';
    dismissible?: boolean;
    class?: string;
    children?: import('svelte').Snippet;
    ondismiss?: () => void;
  }

  let {
    variant = 'info',
    dismissible = false,
    class: className,
    children,
    ondismiss,
  }: Props = $props();

  let visible = $state(true);

  const variantClasses = {
    info: 'bg-mcat-bg border-mcat-border text-mcat-text-muted',
    warning: 'bg-amber-500/10 border-amber-500/30 text-amber-400',
    success: 'bg-status-live/10 border-status-live/30 text-status-live',
    error: 'bg-mcat-error-bg border-mcat-error/30 text-mcat-error',
  };

  function handleDismiss() {
    visible = false;
    ondismiss?.();
  }
</script>

{#if visible}
  <div class={cn('p-3 border rounded text-sm relative', variantClasses[variant], className)}>
    {#if dismissible}
      <button
        type="button"
        onclick={handleDismiss}
        class="absolute top-2 right-2 p-1 opacity-60 hover:opacity-100 transition-opacity"
        aria-label="Dismiss"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    {/if}
    {@render children?.()}
  </div>
{/if}

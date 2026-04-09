<script lang="ts">
  import { cn } from '$lib/utils';
  import { X } from 'phosphor-svelte';

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
    info: 'bg-bg-primary border-border-mid text-text-muted',
    warning: 'bg-status-restricted/10 border-status-restricted/30 text-status-restricted',
    success: 'bg-status-live/10 border-status-live/30 text-status-live',
    error: 'bg-status-removed/10 border-status-removed/30 text-status-removed',
  };

  function handleDismiss() {
    visible = false;
    ondismiss?.();
  }
</script>

{#if visible}
  <div class={cn('p-3 border rounded text-base relative', variantClasses[variant], className)}>
    {#if dismissible}
      <button
        type="button"
        onclick={handleDismiss}
        class="absolute top-2 right-2 p-1 opacity-60 hover:opacity-100 transition-opacity"
        aria-label="Dismiss"
      >
        <X size={16} />
      </button>
    {/if}
    {@render children?.()}
  </div>
{/if}

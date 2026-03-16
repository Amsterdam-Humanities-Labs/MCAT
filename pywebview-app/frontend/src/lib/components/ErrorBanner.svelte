<script lang="ts">
  import { cn } from '$lib/utils';
  import { WarningCircle, X } from 'phosphor-svelte';

  interface Props {
    message: string;
    dismissible?: boolean;
    class?: string;
    ondismiss?: () => void;
  }

  let {
    message,
    dismissible = true,
    class: className,
    ondismiss,
  }: Props = $props();
</script>

{#if message}
  <div
    class={cn(
      'flex items-center justify-between gap-4 px-4 py-3 bg-status-removed/10 border border-status-removed/30 rounded-lg',
      className
    )}
    role="alert"
  >
    <div class="flex items-center gap-3">
      <WarningCircle size={20} class="text-status-removed flex-shrink-0" />
      <p class="text-sm text-status-removed">{message}</p>
    </div>

    {#if dismissible && ondismiss}
      <button
        type="button"
        class="p-1 text-status-removed/70 hover:text-status-removed transition-colors"
        onclick={ondismiss}
        aria-label="Dismiss"
      >
        <X size={16} />
      </button>
    {/if}
  </div>
{/if}

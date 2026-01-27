<script lang="ts">
  import { cn } from '$lib/utils';

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
      'flex items-center justify-between gap-4 px-4 py-3 bg-mcat-error-bg border border-mcat-error/30 rounded-lg',
      className
    )}
    role="alert"
  >
    <div class="flex items-center gap-3">
      <svg
        class="w-5 h-5 text-mcat-error flex-shrink-0"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
      <p class="text-sm text-mcat-error">{message}</p>
    </div>

    {#if dismissible && ondismiss}
      <button
        type="button"
        class="p-1 text-mcat-error/70 hover:text-mcat-error transition-colors"
        onclick={ondismiss}
        aria-label="Dismiss"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    {/if}
  </div>
{/if}

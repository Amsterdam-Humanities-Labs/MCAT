<script lang="ts">
  import { cn } from '$lib/utils';
  import { Dialog } from 'melt/builders';
  import { X } from 'phosphor-svelte';

  interface Props {
    open?: boolean;
    title?: string;
    class?: string;
    onclose?: () => void;
    children?: import('svelte').Snippet;
    actions?: import('svelte').Snippet;
  }

  let {
    open = $bindable(false),
    title,
    class: className,
    onclose,
    children,
    actions,
  }: Props = $props();

  const dialog = new Dialog({
    onOpenChange: (isOpen) => {
      if (!isOpen) onclose?.();
    },
  });

  // Sync prop to dialog state
  $effect(() => {
    dialog.open = open;
  });
</script>

<div
  {...dialog.overlay}
  class="fixed inset-0 z-50 bg-black/40 opacity-0 transition-opacity duration-200 data-[open]:opacity-100"
></div>

<dialog
  {...dialog.content}
  class={cn(
    'fixed left-1/2 top-1/2 z-50 -translate-x-1/2 -translate-y-1/2',
    'w-full max-w-lg max-h-[85vh] overflow-auto',
    'bg-bg-controls border border-border-mid rounded-lg shadow-xl',
    'p-0 m-0 opacity-0 scale-95 transition-all duration-200',
    'data-[open]:opacity-100 data-[open]:scale-100',
    className
  )}
>
  <div class="p-6">
    {#if title}
      <h2 class="text-lg font-semibold text-text-body mb-4">
        {title}
      </h2>
    {/if}

    <div class="text-text-body">
      {@render children?.()}
    </div>

    {#if actions}
      <div class="mt-6 flex justify-end gap-3">
        {@render actions?.()}
      </div>
    {/if}
  </div>

  <button
    type="button"
    onclick={() => (dialog.open = false)}
    class="absolute top-4 right-4 p-1 text-text-secondary hover:text-text-body transition-colors"
    aria-label="Close"
  >
    <X size={20} />
  </button>
</dialog>

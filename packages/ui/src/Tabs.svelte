<script lang="ts">
  import { cn } from './utils';

  interface Tab {
    value: string;
    label: string;
    disabled?: boolean;
  }

  interface Props {
    tabs: Tab[];
    value?: string;
    class?: string;
    onchange?: (value: string) => void;
  }

  let {
    tabs: tabItems,
    value = $bindable(tabItems[0]?.value ?? ''),
    class: className,
    onchange,
  }: Props = $props();
</script>

<div class={cn("inline-flex bg-bg-controls rounded p-0.5 gap-0.5", className)}>
  {#each tabItems as tab}
    <button
      disabled={tab.disabled}
      class={cn(
        'px-4 py-2 text-base whitespace-nowrap transition-colors rounded cursor-pointer',
        'focus:outline-none',
        value === tab.value
          ? 'bg-bg-detail text-text-primary border border-accent-primary hover:bg-interactive-input'
          : 'text-text-secondary hover:text-text-primary hover:bg-interactive-hover border border-transparent',
        tab.disabled && 'opacity-50 cursor-not-allowed'
      )}
      onclick={() => { value = tab.value; onchange?.(tab.value); }}
    >
      {tab.label}
    </button>
  {/each}
</div>

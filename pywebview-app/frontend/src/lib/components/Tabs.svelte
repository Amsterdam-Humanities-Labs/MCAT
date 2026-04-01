<script lang="ts">
  import { cn } from '$lib/utils';
  import { Tabs } from 'melt/builders';

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
    children?: import('svelte').Snippet<[string]>;
  }

  let {
    tabs: tabItems,
    value = $bindable(tabItems[0]?.value ?? ''),
    class: className,
    onchange,
    children,
  }: Props = $props();

  const tabs = new Tabs<string>({
    value: () => value,
    onValueChange: (newValue) => {
      value = newValue;
      onchange?.(newValue);
    },
    loop: true,
    orientation: 'horizontal',
  });
</script>

<div class={cn('w-full', className)}>
  <div {...tabs.triggerList} class="flex gap-1 border-b border-border-mid">
    {#each tabItems as tab}
      <button
        {...tabs.getTrigger(tab.value)}
        disabled={tab.disabled}
        class={cn(
          'px-3 py-2 text-sm font-medium transition-colors rounded-t cursor-pointer -mb-px',
          'border border-border-mid focus:outline-none',
          tabs.value === tab.value
            ? 'bg-accent-tab-active text-accent-brown border-b-transparent'
            : 'text-accent-brown hover:bg-interactive-hover border-b-transparent',
          tab.disabled && 'opacity-50 cursor-not-allowed'
        )}
      >
        {tab.label}
      </button>
    {/each}
  </div>

  {#each tabItems as tab}
    <div {...tabs.getContent(tab.value)} class="focus:outline-none">
      {#if tabs.value === tab.value && children}
        {@render children(tab.value)}
      {/if}
    </div>
  {/each}
</div>

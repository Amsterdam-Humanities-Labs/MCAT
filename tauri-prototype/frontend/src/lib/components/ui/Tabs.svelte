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
  <div {...tabs.triggerList} class="flex border-b border-mcat-border mb-4">
    {#each tabItems as tab}
      <button
        {...tabs.getTrigger(tab.value)}
        disabled={tab.disabled}
        class={cn(
          'px-4 py-2 text-sm font-medium transition-colors',
          'border-b-2 -mb-px',
          'focus:outline-none focus:ring-2 focus:ring-mcat-orange focus:ring-inset',
          tabs.value === tab.value
            ? 'border-mcat-orange text-mcat-orange'
            : 'border-transparent text-mcat-text-muted hover:text-mcat-text hover:border-mcat-border-light',
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

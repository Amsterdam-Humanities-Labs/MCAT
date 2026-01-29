<script lang="ts">
  import { cn } from '$lib/utils';
  import Checkbox from './Checkbox.svelte';

  interface Option {
    value: string;
    label: string;
    disabled?: boolean;
  }

  interface Props {
    options: Option[];
    selected?: string[];
    disabled?: boolean;
    layout?: 'vertical' | 'horizontal';
    class?: string;
    onchange?: (selected: string[]) => void;
  }

  let {
    options,
    selected = $bindable([]),
    disabled = false,
    layout = 'vertical',
    class: className,
    onchange,
  }: Props = $props();

  function handleToggle(value: string, checked: boolean) {
    if (checked) {
      if (!selected.includes(value)) {
        selected = [...selected, value];
      }
    } else {
      selected = selected.filter((v) => v !== value);
    }
    onchange?.(selected);
  }
</script>

<div
  class={cn(
    'flex gap-3',
    layout === 'vertical' ? 'flex-col' : 'flex-row flex-wrap',
    className
  )}
>
  {#each options as opt}
    <Checkbox
      checked={selected.includes(opt.value)}
      disabled={disabled || opt.disabled}
      label={opt.label}
      onchange={(checked) => handleToggle(opt.value, checked)}
    />
  {/each}
</div>

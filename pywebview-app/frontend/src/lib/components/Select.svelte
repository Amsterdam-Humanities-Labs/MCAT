<script lang="ts">
  import { cn } from '$lib/utils';
  import { Select } from 'melt/builders';
  import { CaretDown } from 'phosphor-svelte';

  interface Option {
    value: string;
    label: string;
    disabled?: boolean;
  }

  interface Props {
    options: Option[];
    value?: string;
    placeholder?: string;
    disabled?: boolean;
    error?: string | null;
    class?: string;
    onchange?: (value: string) => void;
    onblur?: () => void;
  }

  let {
    options,
    value = $bindable(''),
    placeholder = 'Select...',
    disabled = false,
    error,
    class: className,
    onchange,
    onblur,
  }: Props = $props();

  const select = new Select<string>({
    value: () => value || undefined,
    onValueChange: (newValue) => {
      if (newValue !== undefined && newValue !== null) {
        value = newValue;
        onchange?.(newValue);
      }
    },
  });

  const selectedOption = $derived(options.find((o) => o.value === select.value));
</script>

<div class={cn('relative', className)}>
  <button
    type="button"
    {disabled}
    {...select.trigger}
    onfocusout={(e) => {
      select.trigger.onfocusout(e);
      onblur?.();
    }}
    class={cn(
      'w-full flex items-center justify-between px-3 py-2 bg-bg-controls border rounded text-text-body text-left',
      'focus:outline-none focus:ring-2 focus:ring-accent-brown focus:border-transparent',
      'disabled:opacity-50 disabled:cursor-not-allowed',
      error ? 'border-status-removed' : 'border-border-mid'
    )}
  >
    <span class={selectedOption ? '' : 'text-text-muted'}>
      {selectedOption?.label ?? placeholder}
    </span>
    <CaretDown size={16} class="text-text-muted transition-transform {select.trigger['aria-expanded'] ? 'rotate-180' : ''}" />
  </button>

  <div
    {...select.content}
    class="absolute z-50 mt-1 w-full bg-bg-controls border border-border-mid rounded shadow-lg max-h-60 overflow-auto"
  >
    {#each options as opt}
      <div
        {...select.getOption(opt.value, opt.label)}
        class={cn(
          'px-3 py-2 cursor-pointer text-text-body',
          'hover:bg-border-light',
          'data-[highlighted]:bg-bg-controls',
          select.isSelected(opt.value) && 'bg-accent-brown text-white',
          opt.disabled && 'opacity-50 cursor-not-allowed pointer-events-none'
        )}
      >
        {opt.label}
      </div>
    {/each}
  </div>

  {#if error}
    <p class="mt-1 text-sm text-status-removed">{error}</p>
  {/if}
</div>

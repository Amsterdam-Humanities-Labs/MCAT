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
      'w-full flex items-center justify-between px-3 py-2 bg-accent-secondary-bg border rounded text-text-body text-sm text-left cursor-pointer',
      'hover:bg-interactive-input focus:outline-none focus:ring-2 focus:ring-accent-primary focus:border-transparent',
      'disabled:opacity-50 disabled:cursor-not-allowed',
      error ? 'border-status-removed' : 'border-border-mid'
    )}
  >
    <span class={selectedOption ? '' : 'text-text-muted'}>
      {selectedOption?.label ?? placeholder}
    </span>
    <CaretDown size={16} weight="bold" class="text-text-muted {select.trigger['aria-expanded'] ? 'rotate-180' : ''}" />
  </button>

  <div
    {...select.content}
    class="absolute z-50 mt-1 w-full bg-bg-controls border border-border-mid rounded shadow-lg max-h-60 overflow-auto divide-y divide-border-light"
  >
    {#each options as opt}
      <div
        {...select.getOption(opt.value, opt.label)}
        class={cn(
          'px-3 py-2 text-sm cursor-pointer',
          select.isSelected(opt.value)
            ? 'bg-accent-tab-active text-text-body'
            : 'text-text-body hover:bg-interactive-hover',
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

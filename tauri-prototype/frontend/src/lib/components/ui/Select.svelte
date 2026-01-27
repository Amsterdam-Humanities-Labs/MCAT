<script lang="ts">
  import { cn } from '$lib/utils';
  import { Select } from 'melt/builders';

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
      'w-full flex items-center justify-between px-3 py-2 bg-mcat-card border rounded text-mcat-text text-left',
      'focus:outline-none focus:ring-2 focus:ring-mcat-orange focus:border-transparent',
      'disabled:opacity-50 disabled:cursor-not-allowed',
      error ? 'border-mcat-error' : 'border-mcat-border'
    )}
  >
    <span class={selectedOption ? '' : 'text-mcat-text-muted'}>
      {selectedOption?.label ?? placeholder}
    </span>
    <svg
      class="w-4 h-4 text-mcat-text-muted transition-transform"
      class:rotate-180={select.trigger['aria-expanded']}
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
    >
      <path
        stroke-linecap="round"
        stroke-linejoin="round"
        stroke-width="2"
        d="M19 9l-7 7-7-7"
      />
    </svg>
  </button>

  <div
    {...select.content}
    class="absolute z-50 mt-1 w-full bg-mcat-card border border-mcat-border rounded shadow-lg max-h-60 overflow-auto"
  >
    {#each options as opt}
      <div
        {...select.getOption(opt.value, opt.label)}
        class={cn(
          'px-3 py-2 cursor-pointer text-mcat-text',
          'hover:bg-mcat-border',
          'data-[highlighted]:bg-mcat-border',
          select.isSelected(opt.value) && 'bg-mcat-orange text-white',
          opt.disabled && 'opacity-50 cursor-not-allowed pointer-events-none'
        )}
      >
        {opt.label}
      </div>
    {/each}
  </div>

  {#if error}
    <p class="mt-1 text-sm text-mcat-error">{error}</p>
  {/if}
</div>

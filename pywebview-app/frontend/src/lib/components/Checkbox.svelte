<script lang="ts">
  import { cn } from '$lib/utils';
  import { Check } from 'phosphor-svelte';

  interface Props {
    checked?: boolean;
    disabled?: boolean;
    label?: string;
    size?: 'sm' | 'md';
    class?: string;
    onchange?: (checked: boolean) => void;
  }

  let {
    checked = $bindable(false),
    disabled = false,
    label,
    size = 'md',
    class: className,
    onchange,
  }: Props = $props();

  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-5 h-5',
  };

  function handleClick() {
    if (disabled) return;
    checked = !checked;
    onchange?.(checked);
  }

  function handleKeydown(e: KeyboardEvent) {
    if (disabled) return;
    if (e.key === ' ' || e.key === 'Enter') {
      e.preventDefault();
      handleClick();
    }
  }
</script>

<label class={cn('inline-flex items-center gap-2 cursor-pointer', disabled && 'opacity-50 cursor-not-allowed', className)}>
  <button
    type="button"
    role="checkbox"
    aria-checked={checked}
    {disabled}
    onclick={handleClick}
    onkeydown={handleKeydown}
    class={cn(
      'rounded border flex items-center justify-center transition-colors',
      sizeClasses[size],
      'focus:outline-none focus:ring-2 focus:ring-accent-primary focus:ring-offset-2 focus:ring-offset-bg-primary',
      checked
        ? 'bg-accent-primary border-accent-primary hover:bg-interactive-primary'
        : 'bg-bg-controls border-border-mid hover:border-border-light'
    )}
  >
    {#if checked}
      <Check size={size === 'sm' ? 10 : 12} weight="bold" class="text-white" />
    {/if}
  </button>
  {#if label}
    <span class="text-text-body text-sm">{label}</span>
  {/if}
</label>

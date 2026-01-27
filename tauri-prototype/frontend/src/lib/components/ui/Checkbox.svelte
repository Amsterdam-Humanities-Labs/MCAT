<script lang="ts">
  import { cn } from '$lib/utils';

  interface Props {
    checked?: boolean;
    disabled?: boolean;
    label?: string;
    class?: string;
    onchange?: (checked: boolean) => void;
  }

  let {
    checked = $bindable(false),
    disabled = false,
    label,
    class: className,
    onchange,
  }: Props = $props();

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
      'w-5 h-5 rounded border flex items-center justify-center transition-colors',
      'focus:outline-none focus:ring-2 focus:ring-mcat-orange focus:ring-offset-2 focus:ring-offset-mcat-bg',
      checked
        ? 'bg-mcat-orange border-mcat-orange'
        : 'bg-mcat-card border-mcat-border hover:border-mcat-border-light'
    )}
  >
    {#if checked}
      <svg class="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
      </svg>
    {/if}
  </button>
  {#if label}
    <span class="text-mcat-text text-sm">{label}</span>
  {/if}
</label>

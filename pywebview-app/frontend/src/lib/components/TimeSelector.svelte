<script lang="ts">
  import { cn } from '$lib/utils';

  interface Props {
    value?: number;
    min?: number;
    max?: number;
    disabled?: boolean;
    class?: string;
    onchange?: (value: number) => void;
  }

  let {
    value = $bindable(1),
    min = 1,
    max = 999,
    disabled = false,
    class: className,
    onchange,
  }: Props = $props();

  function handleInput(e: Event) {
    const raw = (e.target as HTMLInputElement).value;
    const v = parseInt(raw);
    if (isNaN(v)) return;
    const clamped = Math.max(min, Math.min(max, v));
    value = clamped;
    (e.target as HTMLInputElement).value = String(clamped);
    onchange?.(clamped);
  }
</script>

<input
  type="text"
  inputmode="numeric"
  {value}
  {disabled}
  oninput={handleInput}
  class={cn(
    'w-16 px-3 py-2 bg-accent-secondary-bg border border-border-mid rounded text-text-body text-sm text-center cursor-pointer',
    'hover:bg-interactive-input focus:outline-none focus:ring-2 focus:ring-accent-primary focus:border-transparent',
    'disabled:opacity-50 disabled:cursor-not-allowed',
    className
  )}
/>

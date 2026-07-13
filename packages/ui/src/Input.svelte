<script lang="ts">
  import { cn } from './utils';

  interface Props {
    value?: string;
    placeholder?: string;
    readonly?: boolean;
    disabled?: boolean;
    error?: string | null;
    type?: 'text' | 'email' | 'password' | 'number' | 'url';
    class?: string;
    oninput?: (e: Event) => void;
    onchange?: (e: Event) => void;
    onblur?: (e: FocusEvent) => void;
  }

  let {
    value = $bindable(''),
    placeholder = '',
    readonly = false,
    disabled = false,
    error,
    type = 'text',
    class: className,
    oninput,
    onchange,
    onblur,
  }: Props = $props();

  const baseClasses =
    'w-full px-3 py-2 bg-bg-detail border rounded text-text-body text-base placeholder-text-secondary cursor-text hover:bg-interactive-input focus:outline-none focus:ring-2 focus:ring-accent-primary focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed';

  const errorClasses = 'border-status-removed focus:ring-status-removed';
  const normalClasses = 'border-border-mid';
</script>

<div class="w-full">
  <input
    {type}
    bind:value
    {placeholder}
    {readonly}
    {disabled}
    class={cn(baseClasses, error ? errorClasses : normalClasses, className)}
    {oninput}
    {onchange}
    {onblur}
  />
  {#if error}
    <p class="mt-1 text-base text-status-removed">{error}</p>
  {/if}
</div>

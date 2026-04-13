<script lang="ts">
  import { cn } from '$lib/utils';

  interface Props {
    label?: string;
    error?: string | null;
    required?: boolean;
    hint?: string;
    class?: string;
    children?: import('svelte').Snippet;
  }

  let {
    label,
    error,
    required = false,
    hint,
    class: className,
    children,
  }: Props = $props();
</script>

<div class={cn('w-full', className)}>
  {#if label}
    <label class={cn('block text-base font-medium mb-1.5', error ? 'text-status-removed' : 'text-text-primary')}>
      {label}
      {#if required}
        <span class="text-accent-primary">*</span>
      {/if}
    </label>
  {/if}

  {@render children?.()}

  {#if hint && !error}
    <p class="mt-1 text-base text-text-secondary">{hint}</p>
  {/if}
</div>

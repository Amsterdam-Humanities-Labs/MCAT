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
    <label class={cn('block text-sm font-medium mb-1.5', error ? 'text-mcat-error' : 'text-mcat-text-label')}>
      {label}
      {#if required}
        <span class="text-mcat-orange">*</span>
      {/if}
    </label>
  {/if}

  {@render children?.()}

  {#if hint && !error}
    <p class="mt-1 text-xs text-mcat-text-muted">{hint}</p>
  {/if}
</div>

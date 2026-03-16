<script lang="ts">
  import { cn } from '$lib/utils';
  import Button from './Button.svelte';

  interface Props {
    submitLabel?: string;
    cancelLabel?: string;
    submitVariant?: 'primary' | 'danger';
    submitDisabled?: boolean;
    submitting?: boolean;
    showCancel?: boolean;
    class?: string;
    onsubmit?: () => void;
    oncancel?: () => void;
  }

  let {
    submitLabel = 'Submit',
    cancelLabel = 'Cancel',
    submitVariant = 'primary',
    submitDisabled = false,
    submitting = false,
    showCancel = true,
    class: className,
    onsubmit,
    oncancel,
  }: Props = $props();
</script>

<div class={cn('flex justify-end gap-3', className)}>
  {#if showCancel}
    <Button variant="secondary" onclick={oncancel} disabled={submitting}>
      {cancelLabel}
    </Button>
  {/if}
  <Button
    variant={submitVariant}
    onclick={onsubmit}
    disabled={submitDisabled || submitting}
    loading={submitting}
  >
    {submitLabel}
  </Button>
</div>

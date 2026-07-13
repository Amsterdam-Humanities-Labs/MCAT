<script lang="ts">
  import { cn } from '$lib/utils';
  import { api } from '$lib/api/client';
  import { Button } from '@mcat/ui';
  import { Input } from '@mcat/ui';

  interface Props {
    value?: string;
    placeholder?: string;
    disabled?: boolean;
    error?: string | null;
    class?: string;
    onchange?: (path: string) => void;
  }

  let {
    value = $bindable(''),
    placeholder = 'Select a folder...',
    disabled = false,
    error,
    class: className,
    onchange,
  }: Props = $props();

  async function pickFolder() {
    try {
      const result = await api.pickFolder();
      if (result.path) {
        value = result.path;
        onchange?.(value);
      }
    } catch (err) {
      console.error('Folder picker error:', err);
    }
  }
</script>

<div class={className}>
  <div class={cn('flex gap-2')}>
    <Input
      bind:value
      {placeholder}
      readonly
      {disabled}
      error={error}
      class="flex-1"
    />
    <Button
      variant="secondary"
      {disabled}
      onclick={pickFolder}
    >
      Browse
    </Button>
  </div>
</div>

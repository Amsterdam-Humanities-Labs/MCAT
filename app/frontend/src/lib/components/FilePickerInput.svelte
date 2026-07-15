<script lang="ts">
  import { cn } from '$lib/utils';
  import { api } from '$lib/api/client';
  import { Button } from '@mcat/shared-ui';
  import { Input } from '@mcat/shared-ui';

  interface FileFilter {
    name: string;
    extensions: string[];
  }

  interface Props {
    value?: string;
    placeholder?: string;
    filters?: FileFilter[];
    disabled?: boolean;
    error?: string | null;
    class?: string;
    onchange?: (path: string) => void;
  }

  let {
    value = $bindable(''),
    placeholder = 'Select a file...',
    filters = [],
    disabled = false,
    error,
    class: className,
    onchange,
  }: Props = $props();

  async function pickFile() {
    try {
      const result = await api.pickFile(filters.length > 0 ? filters : undefined);
      if (result.path) {
        value = result.path;
        onchange?.(value);
      }
    } catch (err) {
      console.error('File picker error:', err);
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
      onclick={pickFile}
    >
      Browse
    </Button>
  </div>
</div>

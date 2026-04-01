<script lang="ts">
  import { cn } from '$lib/utils';
  import Button from './Button.svelte';

  interface Props {
    onOpenFolder?: () => void;
    class?: string;
  }

  let { onOpenFolder, class: className }: Props = $props();
</script>

<div class={cn("flex items-center justify-end py-2.5", className)}>
  {#if onOpenFolder}
    <Button variant="secondary" size="sm" onclick={onOpenFolder}>
      Run Folder
    </Button>
  {/if}
</div>

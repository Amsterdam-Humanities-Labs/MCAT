<script lang="ts">
  import { cn } from '$lib/utils';
  import { Button } from '$lib/components';
  import { FilePlus, FolderOpen, FileText } from 'phosphor-svelte';

  interface Props {
    class?: string;
    onnewproject?: () => void;
    onopenproject?: () => void;
  }

  let {
    class: className,
    onnewproject,
    onopenproject,
  }: Props = $props();
</script>

<div class={cn('flex items-center justify-center min-h-[60vh]', className)}>
  <div class="bg-bg-controls border border-border-mid rounded-lg p-8 max-w-md w-full text-center">
    <div class="mb-6">
      <div class="w-16 h-16 mx-auto mb-4 rounded-full bg-accent-brown/10 flex items-center justify-center">
        <FileText size={32} class="text-accent-brown" />
      </div>
      <h2 class="text-xl font-semibold text-text-primary mb-2">Welcome to MCAT</h2>
      <p class="text-text-muted text-sm">
        Moderation Content Analysis Tool<br />
        Create a new project or open an existing one to get started.
      </p>
    </div>

    <div class="flex flex-col gap-3">
      <Button variant="primary" size="lg" class="w-full" onclick={onnewproject}>
        <FilePlus size={20} class="mr-2" />
        New Project
      </Button>
      <Button variant="secondary" size="lg" class="w-full" onclick={onopenproject}>
        <FolderOpen size={20} class="mr-2" />
        Open Project
      </Button>
    </div>
  </div>
</div>

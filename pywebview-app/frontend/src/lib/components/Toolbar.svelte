<script lang="ts">
  import { cn } from '$lib/utils';
  import Button from './Button.svelte';

  interface Props {
    projectName: string;
    platform: string;
    urlCount: number;
    projectPath: string;
    onOpenFolder?: () => void;
    onClose?: () => void;
    class?: string;
  }

  let { projectName, platform, urlCount, projectPath, onOpenFolder, onClose, class: className }: Props = $props();

  const csvPath = $derived(`${projectPath}/urls.csv`);
</script>

<div class={cn("h-14 px-4 flex items-center gap-4 bg-bg-toolbar border-b border-border-mid", className)}>
  <span class="text-text-primary font-bold">{projectName}</span>
  <span class="text-border-mid">|</span>
  <span class="text-text-secondary">{platform.charAt(0).toUpperCase() + platform.slice(1)}</span>
  <span class="text-border-mid">|</span>
  <span class="text-text-secondary">{urlCount.toLocaleString()} sources</span>
  <span class="text-border-mid">|</span>
  <span class="text-text-secondary">{projectPath}</span>

  <div class="ml-auto flex items-center gap-2">
    <Button variant="secondary" size="sm" onclick={onOpenFolder}>
      Project Folder
    </Button>
    <Button variant="secondary" size="sm" onclick={onClose}>
      Close
    </Button>
  </div>
</div>

<script lang="ts">
  import Button from './Button.svelte';

  interface Props {
    projectName: string;
    platform: string;
    urlCount: number;
    onOpenFolder?: () => void;
    onClose?: () => void;
  }

  let { projectName, platform, urlCount, onOpenFolder, onClose }: Props = $props();
</script>

<div class="h-12 px-4 flex items-center gap-3 bg-bg-toolbar border-b border-border-mid">
  <span class="text-text-primary font-bold">{projectName}</span>
  <span class="text-border-mid">|</span>
  <span class="text-text-secondary">{platform.charAt(0).toUpperCase() + platform.slice(1)}</span>
  <span class="text-border-mid">|</span>
  <span class="text-text-secondary">{urlCount.toLocaleString()} URLs</span>

  <div class="ml-auto flex items-center gap-2">
    <Button variant="secondary" size="sm" onclick={onOpenFolder}>
      Folder
    </Button>
    <Button variant="secondary" size="sm" onclick={onClose}>
      Close
    </Button>
  </div>
</div>

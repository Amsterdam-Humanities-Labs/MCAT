<script lang="ts">
  import { FolderOpen, X } from 'phosphor-svelte';
  import ToolbarBadge from './ToolbarBadge.svelte';

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
  <span class="text-[18px] font-bold text-text-primary">{projectName}</span>
  <ToolbarBadge {platform} />
  <span class="text-text-secondary">{urlCount.toLocaleString()} URLs</span>

  <div class="ml-auto flex items-center gap-1">
    <button
      class="flex items-center gap-1.5 px-3 py-1.5 rounded text-text-secondary hover:text-text-primary hover:bg-border-light transition-colors cursor-pointer"
      onclick={onOpenFolder}
    >
      <FolderOpen size={18} />
      <span>Folder</span>
    </button>
    <div class="w-px h-5 bg-border-mid mx-1"></div>
    <button
      class="flex items-center gap-1.5 px-3 py-1.5 rounded text-text-secondary hover:text-text-primary hover:bg-border-light transition-colors cursor-pointer"
      onclick={onClose}
    >
      <span>Close</span>
    </button>
  </div>
</div>

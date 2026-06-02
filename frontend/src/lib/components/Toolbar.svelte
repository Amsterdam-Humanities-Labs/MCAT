<script lang="ts">
  import { cn } from '$lib/utils';
  import Button from './Button.svelte';
  import type { AuthInfo } from '$types/project';

  interface Props {
    projectName: string;
    platform: string;
    urlCount: number;
    projectPath: string;
    auth?: AuthInfo;
    onOpenFolder?: () => void;
    onClose?: () => void;
    onSetupBrowser?: () => void;
    onResetBrowser?: () => void;
    class?: string;
  }

  let { projectName, platform, urlCount, projectPath, auth, onOpenFolder, onClose, onSetupBrowser, onResetBrowser, class: className }: Props = $props();

  const hasSetup = $derived(auth?.has_cookies ?? false);

  const setupLabel = $derived.by(() => {
    if (!auth?.captured_at) return '';
    const days = Math.floor((Date.now() - new Date(auth.captured_at).getTime()) / 86400000);
    if (days === 0) return 'Set up today';
    if (days === 1) return 'Set up yesterday';
    return `Set up ${days} days ago`;
  });
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
    {#if hasSetup}
      <span class="text-text-secondary text-base">{setupLabel}</span>
      <Button variant="secondary" size="sm" onclick={onResetBrowser}>
        Reset
      </Button>
    {:else}
      <Button variant="secondary" size="sm" onclick={onSetupBrowser}>
        Set up browser
      </Button>
    {/if}
    <Button variant="secondary" size="sm" onclick={onOpenFolder}>
      Project Folder
    </Button>
    <Button variant="secondary" size="sm" onclick={onClose}>
      Close
    </Button>
  </div>
</div>

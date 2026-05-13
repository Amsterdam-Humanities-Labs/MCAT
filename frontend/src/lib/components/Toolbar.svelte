<script lang="ts">
  import { cn } from '$lib/utils';
  import Button from './Button.svelte';
  import type { AuthInfo } from '$types/project';

  const PLATFORMS_NEEDING_LOGIN = ['instagram', 'facebook', 'tiktok'];

  interface Props {
    projectName: string;
    platform: string;
    urlCount: number;
    projectPath: string;
    auth?: AuthInfo;
    onOpenFolder?: () => void;
    onClose?: () => void;
    onLogin?: () => void;
    onLogout?: () => void;
    class?: string;
  }

  let { projectName, platform, urlCount, projectPath, auth, onOpenFolder, onClose, onLogin, onLogout, class: className }: Props = $props();

  const needsLogin = $derived(PLATFORMS_NEEDING_LOGIN.includes(platform));
  const isLoggedIn = $derived(auth?.has_cookies ?? false);
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
    {#if needsLogin}
      {#if isLoggedIn}
        <span class="text-text-secondary text-base">{auth?.username || 'Logged in'}</span>
        <Button variant="secondary" size="sm" onclick={onLogout}>
          Log out
        </Button>
      {:else}
        <span class="text-text-secondary text-base">Anonymous</span>
        <Button variant="secondary" size="sm" onclick={onLogin}>
          Log in
        </Button>
      {/if}
    {/if}
    <Button variant="secondary" size="sm" onclick={onOpenFolder}>
      Project Folder
    </Button>
    <Button variant="secondary" size="sm" onclick={onClose}>
      Close
    </Button>
  </div>
</div>

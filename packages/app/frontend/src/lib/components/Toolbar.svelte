<script lang="ts">
  import { cn } from '$lib/utils';
  import { Button } from '@mcat/shared-ui';
  import { Tooltip } from '@mcat/shared-ui';
  import { WarningCircle } from 'phosphor-svelte';
  import type { AuthInfo } from '$types/project';

  interface Props {
    projectName: string;
    platform: string;
    urlCount: number;
    projectPath: string;
    auth?: AuthInfo;
    onOpenFolder?: () => unknown;
    onClose?: () => unknown;
    onSetupBrowser?: () => unknown;
    onResetBrowser?: () => unknown;
    class?: string;
  }

  let { projectName, platform, urlCount, projectPath, auth, onOpenFolder, onClose, onSetupBrowser, onResetBrowser, class: className }: Props = $props();

  // hasSetup (any saved jar) gates the Reset/Set up button and identity label.
  // The consent label is separate: it reflects whether the user actually made a
  // consent choice, not merely that a cookie file exists (sites auto-set tokens).
  const hasSetup = $derived(auth?.has_cookies ?? false);
  const identityLabel = $derived(
    auth?.username ? `Logged in: ${auth.username}` : auth?.logged_in ? 'Logged in' : 'Anonymous'
  );
  const consentLabel = $derived(auth?.consent_captured ? 'Consent saved' : 'Consent not set');

  // Capture date lives in a tooltip rather than a visible label.
  const captureTooltip = $derived.by(() => {
    if (!auth?.captured_at) return undefined;
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
    <span class="text-text-secondary">{identityLabel}</span>
    <span class="text-border-mid">|</span>
    <span class="text-text-secondary" title={captureTooltip}>{consentLabel}</span>
    {#if hasSetup}
      <Button variant="secondary" size="sm" onclick={onResetBrowser}>
        Reset browser
      </Button>
    {:else}
      <Tooltip text="Never use your real platform account. Scraping can get it banned, so create a separate account just for MCAT.">
        <WarningCircle size={18} class="text-status-removed" />
      </Tooltip>
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

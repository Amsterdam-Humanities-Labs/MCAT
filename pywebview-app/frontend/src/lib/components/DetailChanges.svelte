<script lang="ts">
  import { cn } from '$lib/utils';
  import type { Run } from '$types/project';
  import { colors } from '$lib/theme';
  import { Image } from 'phosphor-svelte';

  interface Change {
    url: string;
    previous_status: string;
    new_status: string;
    timestamp: string;
    screenshot_path: string;
  }

  interface TransitionGroup {
    from: string;
    to: string;
    label: string;
    color: string;
    items: { url: string; screenshot_path: string }[];
  }

  interface Props {
    run: Run;
    changes: Change[];
    loading: boolean;
    error: string | null;
    onOpenScreenshot?: (path: string) => void;
    class?: string;
  }

  let { run, changes, loading, error, onOpenScreenshot, class: className }: Props = $props();

  function statusColor(status: string): string {
    switch (status.toLowerCase()) {
      case 'removed': return colors.status.removed;
      case 'live': return colors.status.live;
      case 'restricted': case 'private': return colors.status.restricted;
      default: return colors.text.hint;
    }
  }

  function statusLabel(s: string): string {
    const map: Record<string, string> = { live: 'Live', removed: 'Removed', restricted: 'Restricted', error: 'Error', private: 'Private' };
    return map[s.toLowerCase()] || s.charAt(0).toUpperCase() + s.slice(1);
  }

  const groups = $derived.by((): TransitionGroup[] => {
    const map = new Map<string, TransitionGroup>();
    for (const c of changes) {
      const key = `${c.previous_status}_to_${c.new_status}`;
      if (!map.has(key)) {
        map.set(key, {
          from: c.previous_status,
          to: c.new_status,
          label: `${statusLabel(c.previous_status)} \u2192 ${statusLabel(c.new_status)}`,
          color: statusColor(c.new_status),
          items: [],
        });
      }
      map.get(key)!.items.push({ url: c.url, screenshot_path: c.screenshot_path });
    }
    return [...map.values()].sort((a, b) => b.items.length - a.items.length);
  });
</script>

<div class={cn(className)}>
{#if loading}
  <p class="text-text-muted text-sm py-4">Loading...</p>
{:else if error}
  <p class="text-status-removed text-sm py-4">{error}</p>
{:else if run.is_baseline}
  <div class="py-3 text-sm">
    <p class="text-text-secondary mb-2">Baseline run — initial status of all URLs:</p>
    <div class="flex flex-col gap-1">
      {#if run.status_summary?.live}
        <span style="color: {colors.status.live}">{run.status_summary.live} Live</span>
      {/if}
      {#if run.status_summary?.removed}
        <span style="color: {colors.status.removed}">{run.status_summary.removed} Removed</span>
      {/if}
      {#if run.status_summary?.restricted}
        <span style="color: {colors.status.restricted}">{run.status_summary.restricted} Restricted</span>
      {/if}
      {#if run.status_summary?.error}
        <span style="color: {colors.status.error}">{run.status_summary.error} Error</span>
      {/if}
    </div>
  </div>
{:else if groups.length === 0}
  <p class="text-text-muted text-sm py-4">No changes detected</p>
{:else}
  <div class="flex flex-col gap-4 py-3">
    {#each groups as group}
      <div>
        <div class="flex items-center gap-2 mb-2">
          <span class="text-sm" style="color: {group.color}">{group.items.length} {group.label}</span>
        </div>
        <div class="flex flex-col gap-0.5 ml-5">
          {#each group.items as item}
            <div class="flex items-center gap-2 py-0.5">
              <a
                href={item.url}
                target="_blank"
                rel="noopener"
                class="text-sm truncate"
                style="color: {colors.link}"
              >
                {item.url}
              </a>
              {#if item.screenshot_path}
                <button
                  class="ml-auto shrink-0 cursor-pointer opacity-60 hover:opacity-100"
                  onclick={() => onOpenScreenshot?.(item.screenshot_path)}
                  title="Open screenshot"
                >
                  <Image size={14} />
                </button>
              {/if}
            </div>
          {/each}
        </div>
      </div>
    {/each}
  </div>
{/if}
</div>

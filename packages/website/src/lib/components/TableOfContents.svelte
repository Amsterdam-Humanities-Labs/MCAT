<script lang="ts">
  import { cn } from '@mcat/shared-ui';
  import { MagnifyingGlass } from 'phosphor-svelte';
  import Fuse from 'fuse.js';
  import TocItem from './TocItem.svelte';
  import type { TocEntry } from '$lib/scrollSpy.svelte';

  interface Props {
    headings: TocEntry[];
    activeId: string | null;
    class?: string;
  }

  let { headings, activeId, class: className }: Props = $props();

  let query = $state('');

  const fuse = $derived(new Fuse(headings, { keys: ['text'], threshold: 0.3 }));
  const filtered = $derived(query.trim() ? fuse.search(query).map((r) => r.item) : headings);

  function handleInputKeydown(event: KeyboardEvent) {
    if (event.key === 'Escape' && query) {
      query = '';
      event.stopPropagation();
    }
  }
</script>

<div class={cn('flex flex-col gap-3', className)}>
  <div class="relative">
    <MagnifyingGlass
      size={14}
      class="pointer-events-none absolute left-2 top-1/2 -translate-y-1/2 text-text-hint"
    />
    <input
      type="text"
      bind:value={query}
      onkeydown={handleInputKeydown}
      placeholder="Search…"
      aria-label="Search contents"
      class="w-full rounded border border-border-input bg-interactive-input py-1.5 pl-7 pr-2 text-base text-text-body placeholder:text-text-hint focus:border-accent-primary focus:outline-none"
    />
  </div>

  {#if filtered.length}
    <nav aria-label="On this page">
      <ul class="flex flex-col gap-1">
        {#each filtered as entry (entry.id)}
          <TocItem href={`#${entry.id}`} depth={entry.depth} active={activeId === entry.id}>
            {entry.text}
          </TocItem>
        {/each}
      </ul>
    </nav>
  {:else}
    <p class="text-base text-text-hint">No matches.</p>
  {/if}
</div>

<script lang="ts">
  import { cn } from '@mcat/shared-ui';
  import type { TocEntry } from '$lib/scrollSpy.svelte';

  interface Props {
    toc: TocEntry[];
    activeId: string | null;
    class?: string;
  }

  let { toc, activeId, class: className }: Props = $props();
</script>

<nav class={cn('text-sm', className)} aria-label="On this page">
  <ul class="flex flex-col border-l border-border-light">
    {#each toc as { depth, text, id } (id)}
      <li>
        <a
          href={`#${id}`}
          class={cn(
            '-ml-px block border-l-2 border-transparent py-1 pl-3 text-text-secondary hover:text-text-primary',
            depth === 3 && 'pl-6',
            activeId === id && 'border-accent-primary text-text-primary',
          )}
        >
          {text}
        </a>
      </li>
    {/each}
  </ul>
</nav>

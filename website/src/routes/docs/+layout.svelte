<script lang="ts">
  import { page } from '$app/state';
  import { afterNavigate } from '$app/navigation';
  import { onMount } from 'svelte';
  import TableOfContents from '$components/TableOfContents.svelte';
  import { ScrollSpy } from '$lib/scrollSpy.svelte';

  let { children } = $props();

  const spy = new ScrollSpy();
  let contentEl = $state<HTMLElement>();

  const headings = $derived(page.data.headings ?? []);
  const showToc = $derived((page.data.showToc ?? false) && headings.length > 0);

  function refresh() {
    if (showToc && contentEl) spy.observe(contentEl);
    else spy.disconnect();
  }

  onMount(() => {
    refresh();
    return () => spy.disconnect();
  });
  afterNavigate(() => refresh());
</script>

{#if showToc}
  <div class="gap-10 md:grid md:grid-cols-[1fr_200px]">
    <div class="min-w-0" bind:this={contentEl}>
      <details class="mb-6 md:hidden">
        <summary class="cursor-pointer text-text-secondary">On this page</summary>
        <TableOfContents toc={headings} activeId={spy.activeId} class="mt-2" />
      </details>
      {@render children()}
    </div>
    <aside class="hidden md:block">
      <div class="sticky top-24">
        <TableOfContents toc={headings} activeId={spy.activeId} />
      </div>
    </aside>
  </div>
{:else}
  {@render children()}
{/if}

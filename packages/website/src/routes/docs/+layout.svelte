<script lang="ts">
  import { page } from '$app/state';
  import { afterNavigate } from '$app/navigation';
  import { onMount } from 'svelte';
  import TocPanel from '$components/TocPanel.svelte';
  import TableOfContents from '$components/TableOfContents.svelte';
  import { ScrollSpy } from '$lib/scrollSpy.svelte';

  let { children } = $props();

  const spy = new ScrollSpy();
  let contentEl = $state<HTMLElement>();
  let tocExpanded = $state(true);
  let headerHeight = $state(56);

  const headings = $derived(page.data.headings ?? []);
  const showToc = $derived((page.data.showToc ?? false) && headings.length > 0);

  function refresh() {
    if (showToc && contentEl) spy.observe(contentEl);
    else spy.disconnect();
  }

  onMount(() => {
    refresh();
    tocExpanded = window.matchMedia('(min-width: 768px)').matches;
    headerHeight = document.querySelector('header')?.offsetHeight ?? headerHeight;
    return () => spy.disconnect();
  });
  afterNavigate(() => refresh());
</script>

{#if showToc}
  <div class="relative">
    <TocPanel bind:expanded={tocExpanded} topOffset={headerHeight}>
      <TableOfContents {headings} activeId={spy.activeId} />
    </TocPanel>
    <div bind:this={contentEl}>
      {@render children()}
    </div>
  </div>
{:else}
  {@render children()}
{/if}

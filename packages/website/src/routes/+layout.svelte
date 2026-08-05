<script lang="ts">
  import '../app.css';
  import { page } from '$app/state';
  import { base } from '$app/paths';
  import { afterNavigate } from '$app/navigation';
  import Nav from '$components/Nav.svelte';
  import NavToggle from '$components/NavToggle.svelte';
  import Footer from '$components/Footer.svelte';
  import Head from '$components/Head.svelte';
  import { navLinks } from '$lib/nav';

  let { children } = $props();

  const isHome = $derived(page.route.id === '/');

  // The layout owns the mobile-nav state; Nav/NavToggle receive it as props.
  let mobileNavOpen = $state(false);

  afterNavigate(() => {
    mobileNavOpen = false;
  });
</script>

<Head meta={page.data.meta} pathname={page.url.pathname} />

<div class="flex min-h-screen flex-col {isHome ? 'bg-bg-active' : 'bg-bg-controls'}">
  <header class="sticky top-0 z-40 border-b border-border-light bg-bg-toolbar">
    <div class="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
      <a
        href="{base}/"
        class="inline-block border-b-2 border-transparent pb-[2.5px] text-[22px] font-medium text-text-primary hover:border-accent-primary"
      >
        MCAT
      </a>

      <Nav links={navLinks} currentPath={page.url.pathname} class="hidden md:block" />

      <NavToggle
        open={mobileNavOpen}
        onclick={() => (mobileNavOpen = !mobileNavOpen)}
        class="md:hidden"
      />
    </div>

    {#if mobileNavOpen}
      <Nav
        links={navLinks}
        currentPath={page.url.pathname}
        orientation="vertical"
        class="border-t border-border-light px-4 py-3 md:hidden"
      />
    {/if}
  </header>

  <main class="mx-auto w-full max-w-5xl flex-1 px-4 py-8">
    {@render children()}
  </main>

  <Footer />
</div>

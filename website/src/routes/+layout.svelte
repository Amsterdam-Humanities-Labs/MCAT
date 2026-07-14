<script lang="ts">
  import '../app.css';
  import { page } from '$app/state';
  import { afterNavigate } from '$app/navigation';
  import { Nav, NavToggle, Seo } from '@mcat/ui/website';
  import { navLinks } from '$lib/nav';
  import { resolveSeo } from '$lib/seo';

  let { children } = $props();

  const seo = $derived(resolveSeo(page.data.meta, page.url.pathname));

  // The layout owns the mobile-nav state; Nav/NavToggle receive it as props.
  let mobileNavOpen = $state(false);

  afterNavigate(() => {
    mobileNavOpen = false;
  });
</script>

<Seo {...seo} />

<header class="sticky top-0 z-40 border-b border-border-light bg-bg-primary">
  <div class="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
    <a
      href="/"
      class="border-2 border-text-primary px-2.5 py-0.5 text-lg font-semibold text-text-primary"
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

<main class="mx-auto max-w-5xl px-4 py-8">
  {@render children()}
</main>

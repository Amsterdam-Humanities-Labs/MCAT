<script lang="ts">
  import { Link } from '@mcat/shared-ui';
  import H1 from '$components/H1.svelte';
  import { docs } from '$lib/docs';

  const entries = Object.entries(docs).map(([slug, mod]) => ({
    slug,
    title: (mod.metadata.title as string | undefined) ?? slug,
  }));
</script>

<H1>Documentation</H1>
<ul class="mt-6 flex flex-col gap-2">
  {#each entries as { slug, title } (slug)}
    <li><Link href={`/docs/${slug}`}>{title}</Link></li>
  {/each}
</ul>

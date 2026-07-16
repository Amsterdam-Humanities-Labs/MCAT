<script lang="ts">
  import { site, type PageMeta } from '$lib/seo';

  interface Props {
    meta?: PageMeta;
    pathname: string;
  }

  let { meta, pathname }: Props = $props();

  const title = $derived(meta?.title ?? site.name);
  const description = $derived(meta?.description ?? site.description);
  const canonical = $derived(site.url + pathname);
  const ogImage = $derived(meta?.ogImage ?? site.ogImage);
  const ogImageUrl = $derived(ogImage.startsWith('http') ? ogImage : site.url + ogImage);
</script>

<svelte:head>
  <title>{title}</title>
  <meta name="description" content={description} />
  <link rel="canonical" href={canonical} />
  <meta property="og:type" content="website" />
  <meta property="og:site_name" content={site.name} />
  <meta property="og:title" content={title} />
  <meta property="og:description" content={description} />
  <meta property="og:url" content={canonical} />
  <meta property="og:image" content={ogImageUrl} />
  <meta name="twitter:card" content="summary_large_image" />
</svelte:head>

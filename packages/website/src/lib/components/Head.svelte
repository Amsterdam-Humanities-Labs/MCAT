<script lang="ts">
  import { site, type PageMeta } from '$lib/seo';

  interface Props {
    meta?: PageMeta;
    pathname: string;
  }

  let { meta, pathname }: Props = $props();

  const title = $derived(
    !meta?.title || meta.title === site.name
      ? site.name
      : meta.title.includes(site.name)
        ? meta.title
        : `${meta.title} · ${site.name}`,
  );
  const description = $derived(meta?.description ?? site.description);
  const canonical = $derived(site.url + pathname);
  const ogImage = $derived(meta?.ogImage ?? site.ogImage);
  const ogImageUrl = $derived(
    ogImage.startsWith('http') ? ogImage : site.url + site.basePath + ogImage,
  );
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
  <meta property="og:locale" content={site.locale} />
  <meta property="og:image" content={ogImageUrl} />
  <meta property="og:image:type" content="image/jpeg" />
  <meta property="og:image:width" content={String(site.ogImageWidth)} />
  <meta property="og:image:height" content={String(site.ogImageHeight)} />
  <meta property="og:image:alt" content={site.ogImageAlt} />

  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content={title} />
  <meta name="twitter:description" content={description} />
  <meta name="twitter:image" content={ogImageUrl} />
  <meta name="twitter:image:alt" content={site.ogImageAlt} />
</svelte:head>

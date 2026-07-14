<script lang="ts">
  // Presentational: the consumer resolves page metadata against its site config
  // and passes the final values in.
  interface Props {
    title: string;
    description: string;
    canonical: string;
    ogImage: string;
    siteName: string;
  }

  let { title, description, canonical, ogImage, siteName }: Props = $props();
</script>

<svelte:head>
  <title>{title}</title>
  <meta name="description" content={description} />
  <link rel="canonical" href={canonical} />
  <meta property="og:type" content="website" />
  <meta property="og:site_name" content={siteName} />
  <meta property="og:title" content={title} />
  <meta property="og:description" content={description} />
  <meta property="og:url" content={canonical} />
  <meta property="og:image" content={ogImage} />
  <meta name="twitter:card" content="summary_large_image" />
</svelte:head>

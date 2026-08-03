<script lang="ts">
  import { Button } from '@mcat/shared-ui';
  import { base } from '$app/paths';
  import H1 from '$components/H1.svelte';
  import P from '$components/P.svelte';
  import type { PageData } from './$types';

  let { data }: { data: PageData } = $props();

  const downloadUrl =
    'https://github.com/Amsterdam-Humanities-Labs/MCAT/releases/latest/download/MCAT-macOS-arm64.zip';
</script>

<section class="grid gap-8 md:grid-cols-2 md:items-center">
  <div class="flex flex-col gap-5">
    <H1>{data.headline}</H1>
    <P>{data.tagline}</P>
    <div class="flex flex-wrap gap-3">
      <Button href={downloadUrl} variant="primary">Download</Button>
      <Button href="{base}/docs" variant="secondary">Documentation</Button>
    </div>
  </div>

  <div class="aspect-video w-full rounded border border-border-light bg-bg-detail"></div>
</section>

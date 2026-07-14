<script lang="ts">
  import { Button } from '@mcat/ui';
  import { H1, P } from '@mcat/ui/website';
  import type { PageData } from './$types';

  let { data }: { data: PageData } = $props();

  // TODO: point at the real repo once releases are published.
  const downloadUrl = 'https://github.com/OWNER/MCAT/releases/latest';
</script>

<section class="grid gap-8 md:grid-cols-2 md:items-center">
  <div class="flex flex-col gap-5">
    <H1>{data.headline}</H1>
    <P>{data.tagline}</P>
    <div class="flex flex-wrap gap-3">
      <Button href={downloadUrl} variant="primary">Download</Button>
      <Button href="/docs" variant="secondary">Documentation</Button>
    </div>
  </div>

  <div class="aspect-video w-full rounded border border-border-light bg-bg-detail"></div>
</section>

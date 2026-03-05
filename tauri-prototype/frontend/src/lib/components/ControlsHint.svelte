<script lang="ts">
  import { formatDuration } from '$lib/utils/format';

  interface Props {
    durationSeconds: number | null;
  }

  let { durationSeconds }: Props = $props();

  const text = $derived(
    durationSeconds ? `Last run took ${formatDuration(durationSeconds)}` : ''
  );
</script>

{#if text}
  <span class="text-text-hint">{text}</span>
{/if}

<script lang="ts">
  interface Props {
    platform: string;
  }

  let { platform }: Props = $props();
</script>

<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-[14px] font-semibold bg-accent-brown text-bg-primary">
  {platform.charAt(0).toUpperCase() + platform.slice(1)}
</span>

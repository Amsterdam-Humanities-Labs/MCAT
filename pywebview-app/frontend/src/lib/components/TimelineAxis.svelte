<script lang="ts">
  interface Props {
    width: number;
  }

  let { width }: Props = $props();
</script>

<div class="absolute top-0 left-0 pointer-events-none flex items-center" style="width: {width}px;">
  <div class="flex-1 h-[1.5px] bg-[#C4AD8A]"></div>
  <span class="text-[#C4AD8A] text-[8px] leading-none -ml-1">&#x25B6;</span>
</div>

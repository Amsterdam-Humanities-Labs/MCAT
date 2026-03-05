<script lang="ts">
  interface Props {
    width: number;
  }

  let { width }: Props = $props();
</script>

<svg class="absolute top-0 left-0 pointer-events-none" {width} height="1" style="overflow: visible">
  <line x1="0" y1="0" x2={width - 12} y2="0" stroke="#C4AD8A" stroke-width="1.5" />
  <polygon points="{width - 12},-4 {width},0 {width - 12},4" fill="#C4AD8A" />
</svg>

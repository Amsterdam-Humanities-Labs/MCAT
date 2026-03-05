<script lang="ts">
  import type { Run } from '$types/project';
  import TimelineLabel from './TimelineLabel.svelte';

  interface Props {
    run: Run;
    isSelected: boolean;
    onClick?: () => void;
  }

  let { run, isSelected, onClick }: Props = $props();

  const isNoChange = $derived(!run.isBaseline && run.changesCount === 0);
  const radius = $derived(isNoChange ? 5 : 7);
  const fillColor = $derived(isNoChange ? '#C4AD8A' : '#6B4C2A');
</script>

<button type="button" class="flex flex-col items-center cursor-pointer bg-transparent border-none p-0" onclick={onClick}>
  <svg width={radius * 2 + 8} height={radius * 2 + 8} style="overflow: visible">
    {#if isSelected}
      <circle cx={radius + 4} cy={radius + 4} r={radius + 3} fill="none" stroke="#6B4C2A" stroke-width="2" />
    {/if}
    <circle cx={radius + 4} cy={radius + 4} r={radius} fill={fillColor} />
  </svg>
  <TimelineLabel {run} />
</button>

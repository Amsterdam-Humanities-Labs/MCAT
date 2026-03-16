<script lang="ts">
  import type { Run } from '$types/project';
  import TimelineLabel from './TimelineLabel.svelte';

  interface Props {
    run: Run;
    isSelected: boolean;
    onClick?: () => void;
  }

  let { run, isSelected, onClick }: Props = $props();

  const isNoChange = $derived(!run.is_baseline && run.changes_count === 0);
  const dotSize = $derived(isNoChange ? 'text-[10px]' : 'text-[14px]');
  const dotColor = $derived(isNoChange ? 'text-[#C4AD8A]' : 'text-[#6B4C2A]');
</script>

<button type="button" class="flex flex-col items-center cursor-pointer bg-transparent border-none p-0" onclick={onClick}>
  <span class="relative inline-flex items-center justify-center w-6 h-6">
    {#if isSelected}
      <span class="absolute inset-0 rounded-full border-2 border-[#6B4C2A]"></span>
    {/if}
    <span class="{dotSize} {dotColor} leading-none">&#x25CF;</span>
  </span>
  <TimelineLabel {run} />
</button>

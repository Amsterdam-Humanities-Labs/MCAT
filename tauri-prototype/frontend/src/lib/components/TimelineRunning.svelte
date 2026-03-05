<script lang="ts">
  import { formatTimestamp } from '$lib/utils/format';

  interface Props {
    timestamp: string;
    progressPercent: number;
  }

  let { timestamp, progressPercent }: Props = $props();
</script>

<div class="flex flex-col items-center">
  <svg width="22" height="22" style="overflow: visible">
    <circle
      cx="11"
      cy="11"
      r="7"
      fill="none"
      stroke="#6B4C2A"
      stroke-width="1.5"
      stroke-dasharray="4 3"
    >
      <animateTransform
        attributeName="transform"
        type="rotate"
        from="0 11 11"
        to="360 11 11"
        dur="3s"
        repeatCount="indefinite"
      />
    </circle>
  </svg>
  <div class="flex flex-col items-center text-center gap-0.5 mt-3">
    <span class="text-text-secondary text-[14px]">{formatTimestamp(timestamp)}</span>
    <span class="text-text-hint">Running... {progressPercent}%</span>
  </div>
</div>

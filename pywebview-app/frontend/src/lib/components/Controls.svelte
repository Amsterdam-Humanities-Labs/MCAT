<script lang="ts">
  import ControlsStartButton from './ControlsStartButton.svelte';
  import ControlsInterval from './ControlsInterval.svelte';
  import ControlsHint from './ControlsHint.svelte';

  interface Props {
    runState: 'idle' | 'running' | 'paused';
    intervalEnabled: boolean;
    intervalValue: number;
    intervalUnit: 'minutes' | 'hours' | 'days';
    lastRunDuration: number | null;
    onStart?: () => void;
    onPause?: () => void;
    onResume?: () => void;
    onCancel?: () => void;
    onIntervalToggle?: (enabled: boolean) => void;
    onIntervalChange?: (value: number, unit: 'minutes' | 'hours' | 'days') => void;
  }

  let {
    runState,
    intervalEnabled,
    intervalValue,
    intervalUnit,
    lastRunDuration,
    onStart,
    onPause,
    onResume,
    onCancel,
    onIntervalToggle,
    onIntervalChange,
  }: Props = $props();
</script>

<div class="h-14 px-4 flex items-center gap-4 bg-bg-controls border-b border-border-mid">
  <ControlsStartButton {runState} {onStart} {onPause} {onResume} {onCancel} />
  <ControlsInterval
    enabled={intervalEnabled}
    value={intervalValue}
    unit={intervalUnit}
    onToggle={onIntervalToggle}
    onChange={onIntervalChange}
  />
  <ControlsHint durationSeconds={lastRunDuration} />
</div>

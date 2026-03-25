<script lang="ts">
  import ControlsStartButton from './ControlsStartButton.svelte';
  import ControlsInterval from './ControlsInterval.svelte';
  import ControlsHint from './ControlsHint.svelte';
  import ControlsRepeatStatus from './ControlsRepeatStatus.svelte';

  interface Props {
    runState: 'idle' | 'running' | 'paused';
    intervalEnabled: boolean;
    intervalValue: number;
    intervalUnit: 'minutes' | 'hours' | 'days';
    lastRunDuration: number | null;
    nextCheck: string | null;
    onStart?: () => void;
    onPause?: () => void;
    onResume?: () => void;
    onIntervalToggle?: (enabled: boolean) => void;
    onIntervalChange?: (value: number, unit: 'minutes' | 'hours' | 'days') => void;
  }

  let {
    runState,
    intervalEnabled,
    intervalValue,
    intervalUnit,
    lastRunDuration,
    nextCheck,
    onStart,
    onPause,
    onResume,
    onIntervalToggle,
    onIntervalChange,
  }: Props = $props();
</script>

<div class="h-14 px-4 flex items-center gap-4 bg-bg-controls border-b border-border-mid">
  <ControlsStartButton {runState} {onStart} {onPause} {onResume} />
  <ControlsInterval
    enabled={intervalEnabled}
    value={intervalValue}
    unit={intervalUnit}
    onToggle={onIntervalToggle}
    onChange={onIntervalChange}
  />
  <ControlsHint durationSeconds={lastRunDuration} />
  <div class="ml-auto">
    <ControlsRepeatStatus
      enabled={intervalEnabled}
      {nextCheck}
      isRunning={runState === 'running' || runState === 'paused'}
    />
  </div>
</div>

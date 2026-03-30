<script lang="ts">
  import { cn } from '$lib/utils';
  import ControlsStartButton from './ControlsStartButton.svelte';
  import ControlsInterval from './ControlsInterval.svelte';
  import ControlsHint from './ControlsHint.svelte';
  import ControlsTrackingStatus from './ControlsTrackingStatus.svelte';
  import Checkbox from './Checkbox.svelte';

  interface Props {
    runState: 'idle' | 'running' | 'paused';
    intervalEnabled: boolean;
    intervalValue: number;
    intervalUnit: 'minutes' | 'hours' | 'days';
    screenshotsEnabled: boolean;
    lastRunDuration: number | null;
    nextCheck: string | null;
    runNumber: number;
    onStart?: () => void;
    onPause?: () => void;
    onResume?: () => void;
    onIntervalToggle?: (enabled: boolean) => void;
    onIntervalChange?: (value: number, unit: 'minutes' | 'hours' | 'days') => void;
    onScreenshotsToggle?: (enabled: boolean) => void;
    class?: string;
  }

  let {
    runState,
    intervalEnabled,
    intervalValue,
    intervalUnit,
    screenshotsEnabled,
    lastRunDuration,
    nextCheck,
    runNumber,
    onStart,
    onPause,
    onResume,
    onIntervalToggle,
    onIntervalChange,
    onScreenshotsToggle,
    class: className,
  }: Props = $props();
</script>

<div class={cn("h-14 px-4 flex items-center gap-4 bg-bg-controls border-b border-border-mid", className)}>
  <ControlsStartButton {runState} {onStart} {onPause} {onResume} />
  <ControlsInterval
    enabled={intervalEnabled}
    value={intervalValue}
    unit={intervalUnit}
    onToggle={onIntervalToggle}
    onChange={onIntervalChange}
  />
  <Checkbox
    checked={screenshotsEnabled}
    label="Save screenshots"
    size="sm"
    onchange={(checked) => onScreenshotsToggle?.(checked)}
  />
  <ControlsHint durationSeconds={lastRunDuration} />
  <div class="ml-auto">
    <ControlsTrackingStatus
      enabled={intervalEnabled}
      {nextCheck}
      isRunning={runState === 'running' || runState === 'paused'}
      {runNumber}
    />
  </div>
</div>

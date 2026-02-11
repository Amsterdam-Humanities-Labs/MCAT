/**
 * Tracking store for managing URL tracking state.
 */

import { api } from '$lib/api/client';

export interface TrackingState {
  enabled: boolean;
  intervalMinutes: number;
  lastCheck: string | null;
  nextCheck: string | null;
}

export function createTrackingStore() {
  let state = $state<TrackingState>({
    enabled: false,
    intervalMinutes: 60,
    lastCheck: null,
    nextCheck: null,
  });

  return {
    // Getters
    get enabled() {
      return state.enabled;
    },
    get intervalMinutes() {
      return state.intervalMinutes;
    },
    get lastCheck() {
      return state.lastCheck;
    },
    get nextCheck() {
      return state.nextCheck;
    },

    // Actions
    async startTracking(intervalMinutes: number) {
      const result = await api.startTracking(intervalMinutes);
      state.enabled = true;
      state.intervalMinutes = intervalMinutes;
      state.nextCheck = result.next_check;
    },

    async stopTracking() {
      await api.stopTracking();
      state.enabled = false;
    },

    async loadStatus() {
      const result = await api.getTrackingStatus();
      state.enabled = result.enabled;
      state.intervalMinutes = result.interval_minutes;
      state.lastCheck = result.last_check;
      state.nextCheck = result.next_check;
    },

    updateFromSSE(data: any) {
      // Update state from SSE events
      if (data.enabled !== undefined) state.enabled = data.enabled;
      if (data.interval_minutes !== undefined) state.intervalMinutes = data.interval_minutes;
      if (data.last_check !== undefined) state.lastCheck = data.last_check;
      if (data.next_check !== undefined) state.nextCheck = data.next_check;
    },
  };
}

export const trackingStore = createTrackingStore();

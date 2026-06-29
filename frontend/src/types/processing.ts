export type ProcessingState =
  | 'idle'
  | 'processing'
  | 'paused'
  | 'completed'
  | 'cancelled'
  | 'error';

// States where a new processing run can be started
export const IDLE_STATES: ProcessingState[] = ['idle', 'completed', 'cancelled', 'error'];

// States where processing is actively running
export const ACTIVE_STATES: ProcessingState[] = ['processing'];

// States where processing is paused
export const PAUSED_STATES: ProcessingState[] = ['paused'];

export type ContentStatus =
  | 'live'
  | 'unavailable'
  | 'moderated'
  | 'restricted'
  | 'login_required'
  | 'unknown'
  | 'error';

export interface StartProcessingRequest {
  urls?: string[];
  screenshots?: boolean;
}

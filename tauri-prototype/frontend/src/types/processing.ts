export type ProcessingState =
  | 'idle'
  | 'processing'
  | 'paused'
  | 'completed'
  | 'cancelled'
  | 'error';

export interface ProcessingStats {
  [key: string]: number;
}

export interface ProcessingStatus {
  state: ProcessingState;
  total: number;
  processed: number;
  stats: ProcessingStats;
  action: string;
  error: string | null;
}

export interface StartProcessingRequest {
  urls?: string[];
  screenshots?: boolean;
}

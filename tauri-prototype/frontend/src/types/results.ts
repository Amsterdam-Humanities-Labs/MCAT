export type ContentStatus = 'live' | 'removed' | 'restricted' | 'error' | 'pending';

export interface ResultRow {
  url: string;
  status: ContentStatus;
  info: string;
  timestamp: string;
  errorMessage?: string;
}

export interface StatusCounts {
  live: number;
  removed: number;
  restricted: number;
  error: number;
  pending: number;
}

export interface CombinedResults {
  results: ResultRow[];
  byStatus: StatusCounts;
}

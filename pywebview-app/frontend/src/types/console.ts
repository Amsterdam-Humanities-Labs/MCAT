export type LogLevel = 'debug' | 'info' | 'warning' | 'error' | 'success';
export type LogSource = 'app' | 'backend' | 'processing';

export interface LogMessage {
  id: number;
  text: string;
  level: LogLevel;
  source: LogSource;
  timestamp: Date;
}

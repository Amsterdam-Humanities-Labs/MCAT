import { api } from '../api/client';

export interface LogMessage {
  id: number;
  text: string;
  level: 'info' | 'warning' | 'error' | 'success';
  timestamp: Date;
}

const MAX_MESSAGES = 500;

function createConsoleStore() {
  let messages = $state<LogMessage[]>([]);
  let nextId = $state(0);

  return {
    get messages() {
      return messages;
    },

    add(text: string, level: LogMessage['level'] = 'info') {
      const message: LogMessage = {
        id: nextId++,
        text,
        level,
        timestamp: new Date(),
      };

      messages = [...messages, message];

      // Trim if over max
      if (messages.length > MAX_MESSAGES) {
        messages = messages.slice(-MAX_MESSAGES);
      }
    },

    info(text: string) {
      this.add(text, 'info');
    },

    warning(text: string) {
      this.add(text, 'warning');
    },

    error(text: string) {
      this.add(text, 'error');
    },

    success(text: string) {
      this.add(text, 'success');
    },

    clear() {
      messages = [];
    },

    async loadFromBackend() {
      try {
        const response = await api.getLogs();
        messages = response.logs.map((log, index) => ({
          id: index,
          text: log.text,
          level: log.level,
          timestamp: new Date(log.timestamp),
        }));
        nextId = messages.length;
      } catch (e) {
        console.error('Failed to load logs:', e);
      }
    },
  };
}

export const consoleStore = createConsoleStore();

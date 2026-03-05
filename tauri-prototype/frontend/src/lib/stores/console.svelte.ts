import type { LogLevel, LogSource, LogMessage } from '../../types/console';

export type { LogLevel, LogSource, LogMessage };

const MAX_MESSAGES = 500;

function createConsoleStore() {
  let messages = $state<LogMessage[]>([]);
  let nextId = $state(0);
  let showDebug = $state(false);
  let lastBackendLogId = $state(-1);

  function add(text: string, level: LogLevel = 'info', source: LogSource = 'app') {
    const message: LogMessage = {
      id: nextId++,
      text,
      level,
      source,
      timestamp: new Date(),
    };

    messages = [...messages, message];

    // Trim if over max
    if (messages.length > MAX_MESSAGES) {
      messages = messages.slice(-MAX_MESSAGES);
    }
  }

  return {
    get messages() {
      return messages;
    },

    get filteredMessages() {
      if (showDebug) return messages;
      return messages.filter((m) => m.level !== 'debug');
    },

    get showDebug() {
      return showDebug;
    },

    setShowDebug(value: boolean) {
      showDebug = value;
    },

    toggleDebug() {
      showDebug = !showDebug;
    },

    add,

    debug(text: string, source: LogSource = 'app') {
      add(text, 'debug', source);
    },

    info(text: string, source: LogSource = 'app') {
      add(text, 'info', source);
    },

    warning(text: string, source: LogSource = 'app') {
      add(text, 'warning', source);
    },

    error(text: string, source: LogSource = 'app') {
      add(text, 'error', source);
    },

    success(text: string, source: LogSource = 'app') {
      add(text, 'success', source);
    },

    // Log processing events
    processingStarted(total: number) {
      add(`Processing started: ${total} URLs to check`, 'info', 'processing');
    },

    processingProgress(url: string, status: string, current: number, total: number) {
      const shortUrl = url.length > 50 ? url.substring(0, 50) + '...' : url;
      add(`[${current}/${total}] ${shortUrl} → ${status}`, 'info', 'processing');
    },

    processingCompleted(stats: { live: number; removed: number; restricted: number; error: number }) {
      add(
        `Processing completed: ${stats.live} live, ${stats.removed} removed, ${stats.restricted} restricted, ${stats.error} errors`,
        'success',
        'processing'
      );
    },

    processingError(error: string) {
      add(`Processing error: ${error}`, 'error', 'processing');
    },

    processingPaused() {
      add('Processing paused', 'warning', 'processing');
    },

    processingResumed() {
      add('Processing resumed', 'info', 'processing');
    },

    processingCancelled() {
      add('Processing cancelled', 'warning', 'processing');
    },

    addBackendLog(log: { id: number; text: string; level: LogLevel; timestamp: string }) {
      if (log.id > lastBackendLogId) {
        add(log.text, log.level, 'backend');
        lastBackendLogId = log.id;
      }
    },

    clear() {
      messages = [];
      lastBackendLogId = -1;
    },
  };
}

export const consoleStore = createConsoleStore();

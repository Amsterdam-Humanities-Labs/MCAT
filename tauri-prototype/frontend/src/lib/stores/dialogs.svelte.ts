export interface InterruptedRun {
  runId: string;
  processed: number;
  total: number;
  remaining: number;
}

function createDialogsStore() {
  let interruptedRunOpen = $state(false);
  let interruptedRun = $state<InterruptedRun | null>(null);
  let addUrlsOpen = $state(false);

  return {
    // Interrupted Run Dialog
    get interruptedRunOpen() {
      return interruptedRunOpen;
    },
    get interruptedRun() {
      return interruptedRun;
    },
    showInterruptedRun(run: InterruptedRun) {
      interruptedRun = run;
      interruptedRunOpen = true;
    },
    closeInterruptedRun() {
      interruptedRunOpen = false;
      interruptedRun = null;
    },

    // Add URLs Dialog
    get addUrlsOpen() {
      return addUrlsOpen;
    },
    openAddUrls() {
      addUrlsOpen = true;
    },
    closeAddUrls() {
      addUrlsOpen = false;
    },

    // Close all
    closeAll() {
      interruptedRunOpen = false;
      interruptedRun = null;
      addUrlsOpen = false;
    },
  };
}

export const dialogsStore = createDialogsStore();

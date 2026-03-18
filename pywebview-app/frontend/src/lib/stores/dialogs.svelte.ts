function createDialogsStore() {
  let addUrlsOpen = $state(false);

  return {
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
      addUrlsOpen = false;
    },
  };
}

export const dialogsStore = createDialogsStore();

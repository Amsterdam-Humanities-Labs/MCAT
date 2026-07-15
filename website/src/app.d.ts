declare global {
  namespace App {
    interface PageData {
      meta?: import('./lib/seo').PageMeta;
      headings?: import('./lib/scrollSpy.svelte').TocEntry[];
      showToc?: boolean;
    }
  }
}

export {};

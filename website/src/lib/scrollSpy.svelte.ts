// Owns the "currently-read" heading id as $state. The docs layout instantiates
// one and passes `activeId` down to the TOC — no store import in the leaf.
export class ScrollSpy {
  activeId = $state<string | null>(null);
  #observer: IntersectionObserver | null = null;

  observe(container: HTMLElement, topOffset = 96) {
    this.disconnect();
    const headings = Array.from(
      container.querySelectorAll<HTMLElement>('h2[id], h3[id]'),
    );
    if (headings.length === 0) return;

    const visible = new Set<string>();
    this.#observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          const id = entry.target.id;
          if (entry.isIntersecting) visible.add(id);
          else visible.delete(id);
        }
        this.#pick(headings, visible, topOffset);
      },
      { rootMargin: `-${topOffset}px 0px -65% 0px`, threshold: 0 },
    );
    for (const heading of headings) this.#observer.observe(heading);
  }

  #pick(headings: HTMLElement[], visible: Set<string>, topOffset: number) {
    const firstVisible = headings.find((h) => visible.has(h.id));
    if (firstVisible) {
      this.activeId = firstVisible.id;
      return;
    }
    // Nothing in the band: highlight the last heading scrolled past.
    let above: string | null = null;
    for (const heading of headings) {
      if (heading.getBoundingClientRect().top - topOffset < 0) above = heading.id;
      else break;
    }
    this.activeId = above;
  }

  disconnect() {
    this.#observer?.disconnect();
    this.#observer = null;
  }
}

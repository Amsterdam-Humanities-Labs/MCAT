"""Test doubles standing in for zendriver's Tab / BrowserSession.

`FakeTab.evaluate` routes the scrapers' JS snippets to scripted return values by
matching stable substrings; `query_selector` returns scripted elements. The same
tab is reused by detection tests (evaluate/query_selector) and harness tests
(get/save_screenshot).
"""
import asyncio


class FakeEl:
    """Stand-in for a zendriver element — only `.attrs` is read (meta tags)."""

    def __init__(self, attrs=None):
        self.attrs = attrs or {}


class FakeTab:
    def __init__(self, *, body_text="", title="", h1_text="", warn_text="",
                 img_ready=True, href="", selectors=None, evaluate_hook=None,
                 get_error=None):
        self.body_text = body_text
        self.title = title
        self.h1_text = h1_text
        self.warn_text = warn_text
        self.img_ready = img_ready
        self.href = href
        self.selectors = selectors or {}
        self.evaluate_hook = evaluate_hook   # optional callable(js) -> value | coroutine
        self.get_error = get_error           # exception to raise from get() (load failure)
        self.got = []                        # urls passed to get()
        self.screenshots = []                # paths passed to save_screenshot()

    async def evaluate(self, js):
        if self.evaluate_hook is not None:
            res = self.evaluate_hook(js)
            if asyncio.iscoroutine(res):
                res = await res
            if res is not None:
                return res
        if "body.innerText" in js:
            return self.body_text
        if "ytd-watch-metadata" in js:
            return self.h1_text
        if "warning" in js or "restricted" in js:
            return self.warn_text
        if "naturalWidth" in js:             # _wait_for_render probe
            return self.img_ready
        if "location.href" in js:
            return self.href
        if "document.title" in js:
            return self.title
        return ""

    async def query_selector(self, selector):
        return self.selectors.get(selector)

    async def get(self, url):
        self.got.append(url)
        if self.get_error is not None:
            raise self.get_error

    async def save_screenshot(self, path):
        self.screenshots.append(path)


class FakeSession:
    """Stand-in for BrowserSession — hands out a single FakeTab."""

    def __init__(self, tab):
        self._tab = tab
        self.stopped = False

    async def acquire_tab(self):
        return self._tab

    async def release_tab(self, tab):
        pass

    async def stop(self):
        self.stopped = True

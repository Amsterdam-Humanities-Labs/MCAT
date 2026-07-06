"""Tab-pool recycling in BrowserSession (offline stubs).

Verifies the invariant that release_tab always re-pools exactly one tab (the pool
doubles as the concurrency gate, so losing a slot would deadlock acquire_tab),
and that broken / worn-out tabs are replaced rather than re-pooled.
"""
import asyncio

from core.browser_manager import BrowserSession


class _StubTab:
    def __init__(self, healthy=True):
        self.healthy = healthy
        self.closed = False

    async def evaluate(self, js):
        if not self.healthy:
            raise RuntimeError("detached")
        return 1

    async def close(self):
        self.closed = True


class _StubBrowser:
    def __init__(self):
        self.opened = 0

    async def get(self, url, new_tab=False):
        self.opened += 1
        return _StubTab(healthy=True)


def _session(tabs):
    s = BrowserSession()
    s._browser = _StubBrowser()
    for t in tabs:
        s._all_tabs.append(t)
        s._tabs.put_nowait(t)
    return s


async def test_healthy_tab_repooled_unchanged():
    t = _StubTab(healthy=True)
    s = _session([t])
    await s._tabs.get()                      # simulate acquire
    await s.release_tab(t)
    assert s._tabs.qsize() == 1
    assert (await s._tabs.get()) is t
    assert not t.closed


async def test_broken_tab_recycled_one_slot_preserved():
    bad = _StubTab(healthy=False)
    s = _session([bad])
    await s._tabs.get()
    await s.release_tab(bad)
    assert s._tabs.qsize() == 1              # exactly one back
    fresh = await s._tabs.get()
    assert fresh is not bad and bad.closed
    assert bad not in s._all_tabs and fresh in s._all_tabs


async def test_worn_tab_recycled_at_threshold():
    s = BrowserSession()
    s._browser = _StubBrowser()
    s.RECYCLE_EVERY = 1                      # recycle on first release
    t = _StubTab(healthy=True)
    s._all_tabs.append(t)
    await s.release_tab(t)
    fresh = await s._tabs.get()
    assert fresh is not t and t.closed


async def test_release_while_stopped_repools_without_recycling():
    # During teardown, release must still re-pool (so coroutines blocked on
    # acquire_tab unblock and drain) — just skip the health-check/recycle.
    bad = _StubTab(healthy=False)
    s = _session([bad])
    await s._tabs.get()
    s._stopped = True
    await s.release_tab(bad)
    assert s._tabs.qsize() == 1
    assert (await s._tabs.get()) is bad     # same tab back, not recycled
    assert not bad.closed

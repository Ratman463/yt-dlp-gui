"""Regression tests for the DownloadManager queue.

These cover the bugs the old index-based manager had:
 1. Tasks submitted after the queue drained once were never started
    (_current_index kept growing past the queue).
 2. Cancelling one task killed the whole queue and left the rest stuck.
 3. A queued (not yet started) task could not really be cancelled.
"""
from __future__ import annotations

import threading
import time

import pytest

from yt_dlp_gui.downloader import (
    DownloadManager,
    DownloadState,
    ProgressInfo,
)


class FakeDownloader:
    """Deterministic stand-in for Downloader: reports progress, honours cancel."""

    def __init__(self, on_progress, tick=0.01):
        self._on_progress = on_progress
        self._tick = tick
        self._cancelled = threading.Event()
        self.started = threading.Event()

    def download(self, url, **kwargs):
        # Absorb on_log and any other kwargs the manager injects.
        self._on_progress(url, ProgressInfo(state=DownloadState.EXTRACTING, title=url))
        self.started.set()
        for i in range(1, 11):
            if self._cancelled.wait(self._tick):
                self._on_progress(url, ProgressInfo(
                    state=DownloadState.CANCELLED, title=url,
                ))
                return
            self._on_progress(url, ProgressInfo(
                state=DownloadState.DOWNLOADING, percent=i * 10.0, title=url,
            ))
        self._on_progress(url, ProgressInfo(
            state=DownloadState.FINISHED, title=url, percent=100.0,
        ))

    def cancel(self):
        self._cancelled.set()

    @property
    def is_cancelled(self):
        return self._cancelled.is_set()


class Harness:
    def __init__(self):
        self.lock = threading.Lock()
        self.events = []          # (task_id, url, state)
        self.downloads = []       # (task_id, FakeDownloader)
        self.factory_calls = 0

    def factory(self, on_progress):
        self.factory_calls += 1
        return FakeDownloader(on_progress, tick=0.005)

    def on_event(self, task_id, url, info):
        with self.lock:
            self.events.append((task_id, url, info.state))

    def states_for(self, task_id):
        with self.lock:
            return [s for t, _, s in self.events if t == task_id]

    def wait_for(self, task_id, state, timeout=5.0):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if state in self.states_for(task_id):
                return True
            time.sleep(0.005)
        return False


@pytest.fixture
def harness():
    h = Harness()
    yield h
    # Ensure no worker threads linger between tests.


@pytest.fixture
def manager(harness):
    m = DownloadManager(on_event=harness.on_event,
                        downloader_factory=harness.factory)
    yield m
    m.shutdown()


def params(url):
    return {"url": url, "save_path": "/tmp"}


# ─── The big one ───────────────────────────────────────────────────────────────

def test_task_submitted_after_queue_drains_still_runs(manager, harness):
    """Regression: the old manager skipped everything added after a drain."""
    a = manager.submit(params("A"))
    assert harness.wait_for(a, DownloadState.FINISHED), harness.events

    b = manager.submit(params("B"))
    assert harness.wait_for(b, DownloadState.FINISHED), (
        f"B never started after queue drained: {harness.events}"
    )


def test_tasks_run_sequentially_in_fifo_order(manager, harness):
    ids = [manager.submit(params(f"U{i}")) for i in range(5)]
    for tid in ids:
        assert harness.wait_for(tid, DownloadState.FINISHED), harness.events

    # Every task reports EXTRACTING at least once, all finish exactly once.
    for tid in ids:
        states = harness.states_for(tid)
        assert states.count(DownloadState.FINISHED) == 1


def test_many_rapid_submissions_all_run(manager, harness):
    """Hammering submit() from the UI thread must not lose or duplicate tasks."""
    ids = [manager.submit(params(f"U{i}")) for i in range(30)]
    for tid in ids:
        assert harness.wait_for(tid, DownloadState.FINISHED, timeout=15), harness.events
    assert harness.factory_calls == 30


# ─── Cancellation ──────────────────────────────────────────────────────────────

def test_cancel_queued_task_does_not_affect_current(manager, harness):
    """Cancel a waiting task: it never starts, the current one finishes fine."""
    a = manager.submit(params("A"))
    # Wait until A is actually downloading.
    assert harness.wait_for(a, DownloadState.DOWNLOADING)
    b = manager.submit(params("B"))

    manager.cancel(b)
    assert harness.wait_for(b, DownloadState.CANCELLED)
    time.sleep(0.1)
    assert DownloadState.EXTRACTING not in harness.states_for(b), "B started despite cancel"
    assert manager.pending_count == 0

    assert harness.wait_for(a, DownloadState.FINISHED), harness.events


def test_cancel_current_task_does_not_kill_queue(manager, harness):
    """Regression: cancelling the active download used to stop everything after it."""
    a = manager.submit(params("A"))
    assert harness.wait_for(a, DownloadState.DOWNLOADING)
    b = manager.submit(params("B"))

    manager.cancel(a)
    assert harness.wait_for(a, DownloadState.CANCELLED), harness.events
    # B must still run to completion.
    assert harness.wait_for(b, DownloadState.FINISHED), harness.events


def test_cancel_all_clears_queue_and_cancels_current(manager, harness):
    a = manager.submit(params("A"))
    assert harness.wait_for(a, DownloadState.DOWNLOADING)
    b = manager.submit(params("B"))
    c = manager.submit(params("C"))

    manager.cancel_all()

    assert harness.wait_for(a, DownloadState.CANCELLED)
    assert harness.wait_for(b, DownloadState.CANCELLED)
    assert harness.wait_for(c, DownloadState.CANCELLED)
    time.sleep(0.1)
    assert manager.pending_count == 0
    # Queue is still usable afterwards.
    d = manager.submit(params("D"))
    assert harness.wait_for(d, DownloadState.FINISHED), harness.events


def test_cancel_unknown_task_id_is_noop(manager, harness):
    manager.cancel("does-not-exist")
    a = manager.submit(params("A"))
    assert harness.wait_for(a, DownloadState.FINISHED), harness.events


# ─── Misc ──────────────────────────────────────────────────────────────────────

def test_submit_returns_distinct_task_ids(manager, harness):
    id1 = manager.submit(params("same"))
    id2 = manager.submit(params("same"))
    assert id1 != id2


def test_start_is_idempotent_single_worker(manager, harness):
    manager.start()
    manager.start()
    manager.start()
    a = manager.submit(params("A"))
    assert harness.wait_for(a, DownloadState.FINISHED)
    # Exactly one downloader per task, despite repeated start() calls.
    assert harness.factory_calls == 1


def test_shutdown_stops_worker(manager, harness):
    a = manager.submit(params("A"))
    assert harness.wait_for(a, DownloadState.DOWNLOADING)
    manager.shutdown()
    # Worker thread should exit; pending tasks submitted after are ignored.
    worker = manager._worker
    if worker is not None:
        worker.join(timeout=5)
        assert not worker.is_alive()

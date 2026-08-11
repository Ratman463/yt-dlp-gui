"""Integration test: actually download a small public-domain video.

This test requires network access. It downloads a 1-second Big Buck Bunny
clip from a small test fixture and verifies the file lands on disk.

Marked as integration so it can be skipped in pure-unit contexts:
    pytest -m integration
"""
from __future__ import annotations

import os
import threading
import time
from pathlib import Path

import pytest

from yt_dlp_gui.downloader import Downloader, DownloadState, ProgressInfo


# A small, public-domain sample hosted by yt-dlp's test suite.
# Uses sample-videos from github; if it ever breaks, swap for another
# small public URL. We intentionally do NOT use YouTube here — it requires
# a JS runtime and may need a proxy, which is environment-specific.
SAMPLE_URL = "https://samplelib.com/lib/preview/mp3/sample-3s.mp3"


@pytest.fixture
def captured_progress():
    """Collect all ProgressInfo events sent during a download."""
    events: list[ProgressInfo] = []
    lock = threading.Lock()

    def cb(url, info):
        with lock:
            events.append(info)

    return events, lock, cb


@pytest.mark.integration
def test_download_real_audio(tmp_path, captured_progress):
    """Download a 3-second sample MP3 and verify it appears on disk."""
    events, _, cb = captured_progress
    dl = Downloader(on_progress=cb)

    done = threading.Event()
    error: list = []

    def run():
        try:
            dl.download(
                url=SAMPLE_URL,
                save_path=str(tmp_path),
                format_spec="bestaudio/best",
                proxy=os.environ.get("TEST_PROXY", ""),
                cookies_path="",
                subtitle_langs="",
                write_subtitles=False,
                write_auto_subs=False,
                embed_subtitles=False,
                merge_output_format="mp4",
                js_runtimes="",
                player_client="web",
            )
        except Exception as e:
            error.append(e)
        finally:
            done.set()

    t = threading.Thread(target=run, daemon=True)
    t.start()

    # Wait up to 60 seconds (network dependent)
    assert done.wait(timeout=60), "download did not finish in 60s"
    assert not error, f"download raised: {error}"

    # Should have seen at least EXTRACTING → DOWNLOADING/PROCESSING → FINISHED
    states = [e.state for e in events]
    assert DownloadState.EXTRACTING in states or DownloadState.DOWNLOADING in states, \
        f"never entered extracting/downloading: {states}"
    assert events[-1].state == DownloadState.FINISHED, \
        f"last state was {events[-1].state}, not FINISHED"

    # File should exist in tmp_path
    files = list(tmp_path.glob("*"))
    assert files, f"no files downloaded to {tmp_path}"
    assert any(f.stat().st_size > 0 for f in files), "downloaded file is empty"


@pytest.mark.integration
def test_download_cancel(tmp_path, captured_progress):
    """Cancelling mid-download should produce a CANCELLED state."""
    events, _, cb = captured_progress
    dl = Downloader(on_progress=cb)

    done = threading.Event()

    def run():
        dl.download(
            url=SAMPLE_URL,
            save_path=str(tmp_path),
            format_spec="bestaudio/best",
            proxy=os.environ.get("TEST_PROXY", ""),
            cookies_path="", subtitle_langs="",
            write_subtitles=False, write_auto_subs=False, embed_subtitles=False,
            merge_output_format="mp4", js_runtimes="", player_client="web",
        )
        done.set()

    t = threading.Thread(target=run, daemon=True)
    t.start()

    # Give it a moment to start, then cancel
    time.sleep(0.5)
    dl.cancel()

    assert done.wait(timeout=10), "cancel did not stop the download within 10s"
    states = [e.state for e in events]
    assert DownloadState.CANCELLED in states or DownloadState.ERROR in states, \
        f"cancel did not produce CANCELLED/ERROR: {states}"
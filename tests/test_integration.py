"""Integration test: actually download a small public-domain sample.

Marked as ``integration`` so it can be skipped in pure-unit contexts::

    pytest                  # skips network tests
    pytest -m integration   # runs network tests only

We intentionally do NOT use YouTube here — it requires a JS runtime and
may need a proxy, which is environment-specific. The sample below is a
small public-domain clip hosted by yt-dlp's test suite.
"""
from __future__ import annotations

import os
import threading
import time

import pytest

from yt_dlp_gui.downloader import Downloader, DownloadState, ProgressInfo


# A small, public-domain sample.
SAMPLE_URL = "https://samplelib.com/lib/preview/mp3/sample-3s.mp3"


@pytest.fixture
def captured_progress():
    """Collect every ProgressInfo event sent during a download."""
    events: list[ProgressInfo] = []
    lock = threading.Lock()

    def cb(url, info):
        with lock:
            events.append(info)

    return events, lock, cb


@pytest.mark.integration
def test_download_real_audio(tmp_path, captured_progress):
    """Download a 3-second sample MP3 and verify it lands on disk."""
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

    assert done.wait(timeout=60), "download did not finish in 60s"
    assert not error, f"download raised: {error}"

    states = [e.state for e in events]
    assert (
        DownloadState.EXTRACTING in states
        or DownloadState.DOWNLOADING in states
    ), f"never entered extracting/downloading: {states}"
    assert events[-1].state == DownloadState.FINISHED, \
        f"last state was {events[-1].state}, not FINISHED"

    files = list(tmp_path.glob("*"))
    assert files, f"no files downloaded to {tmp_path}"
    assert any(f.stat().st_size > 0 for f in files), \
        "downloaded file is empty"


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
            cookies_path="",
            subtitle_langs="",
            write_subtitles=False,
            write_auto_subs=False,
            embed_subtitles=False,
            merge_output_format="mp4",
            js_runtimes="",
            player_client="web",
        )
        done.set()

    t = threading.Thread(target=run, daemon=True)
    t.start()

    time.sleep(0.5)
    dl.cancel()

    assert done.wait(timeout=10), "cancel did not stop the download within 10s"
    states = [e.state for e in events]
    assert (
        DownloadState.CANCELLED in states or DownloadState.ERROR in states
    ), f"cancel did not produce CANCELLED/ERROR: {states}"

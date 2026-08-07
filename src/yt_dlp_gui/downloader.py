"""
yt-dlp Python API wrapper for yt-dlp-gui.

Provides a thread-safe downloader that reports progress, handles errors,
and supports cancellation.
"""

from __future__ import annotations

import logging
import threading
import re
from enum import Enum
from typing import Callable, Optional

import yt_dlp

logger = logging.getLogger(__name__)


# ─── Download states ───────────────────────────────────────────────────────────

class DownloadState(Enum):
    """State machine for a download task."""
    QUEUED      = "queued"
    EXTRACTING  = "extracting"
    DOWNLOADING = "downloading"
    PROCESSING = "processing"
    FINISHED    = "finished"
    ERROR       = "error"
    CANCELLED   = "cancelled"


# ─── Progress info ─────────────────────────────────────────────────────────────

class ProgressInfo:
    """Structured progress data passed to UI callbacks."""
    __slots__ = (
        "state", "percent", "speed", "eta", "downloaded_bytes",
        "total_bytes", "title", "error_message",
    )

    def __init__(
        self,
        state: DownloadState = DownloadState.QUEUED,
        percent: float = 0.0,
        speed: str = "",
        eta: str = "",
        downloaded_bytes: int = 0,
        total_bytes: int = 0,
        title: str = "",
        error_message: str = "",
    ):
        self.state = state
        self.percent = percent
        self.speed = speed
        self.eta = eta
        self.downloaded_bytes = downloaded_bytes
        self.total_bytes = total_bytes
        self.title = title
        self.error_message = error_message


# ─── Downloader ────────────────────────────────────────────────────────────────

class Downloader:
    """Wraps yt-dlp Python API with progress callbacks and cancellation support."""

    def __init__(self, on_progress: Callable[[str, ProgressInfo], None]):
        """
        Args:
            on_progress: Callback receiving (url, ProgressInfo).
                         Called from a background thread — must be thread-safe.
        """
        self._on_progress = on_progress
        self._cancel_event = threading.Event()
        self._lock = threading.Lock()

    def download(
        self,
        url: str,
        save_path: str,
        format_spec: str = "bv[height<=1080]+ba/b[height<=1080]/best",
        proxy: str = "",
        cookies_path: str = "",
        subtitle_langs: str = "zh-Hans,zh-Hant,en,ja",
        write_subtitles: bool = True,
        write_auto_subs: bool = True,
        embed_subtitles: bool = True,
        merge_output_format: str = "mp4",
        js_runtimes: str = "node",
        player_client: str = "web",
    ) -> None:
        """Download a single video. Runs on the calling thread (use threading to call)."""
        self._cancel_event.clear()
        self._notify(url, ProgressInfo(state=DownloadState.EXTRACTING, title=url))

        ydl_opts = self._build_opts(
            save_path=save_path,
            format_spec=format_spec,
            proxy=proxy,
            cookies_path=cookies_path,
            subtitle_langs=subtitle_langs,
            write_subtitles=write_subtitles,
            write_auto_subs=write_auto_subs,
            embed_subtitles=embed_subtitles,
            merge_output_format=merge_output_format,
            js_runtimes=js_runtimes,
            player_client=player_client,
            url=url,
        )

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if info:
                    title = info.get("title", url)
                    self._notify(url, ProgressInfo(
                        state=DownloadState.PROCESSING,
                        title=title,
                    ))
                    # yt-dlp handles post-processing internally
                    self._notify(url, ProgressInfo(
                        state=DownloadState.FINISHED,
                        title=title,
                        percent=100.0,
                    ))
        except yt_dlp.utils.DownloadError as e:
            if self._cancel_event.is_set():
                self._notify(url, ProgressInfo(
                    state=DownloadState.CANCELLED,
                    title=url,
                ))
            else:
                self._notify(url, ProgressInfo(
                    state=DownloadState.ERROR,
                    title=url,
                    error_message=str(e),
                ))
        except Exception as e:
            logger.exception("Unexpected download error")
            self._notify(url, ProgressInfo(
                state=DownloadState.ERROR,
                title=url,
                error_message=f"Unexpected error: {e}",
            ))

    def cancel(self) -> None:
        """Signal the current download to stop."""
        self._cancel_event.set()

    @property
    def is_cancelled(self) -> bool:
        return self._cancel_event.is_set()

    # ─── Private ───────────────────────────────────────────────────────────────

    def _notify(self, url: str, info: ProgressInfo) -> None:
        """Thread-safe notification to the UI callback."""
        try:
            self._on_progress(url, info)
        except Exception:
            logger.exception("Error in progress callback")

    def _progress_hook(self, url: str, d: dict) -> None:
        """yt-dlp progress hook — converts raw dicts to ProgressInfo."""
        if self._cancel_event.is_set():
            raise yt_dlp.utils.DownloadError("Download cancelled by user")

        status = d.get("status", "")

        if status == "downloading":
            percent_str = d.get("_percent_str", "0%").strip()
            try:
                percent = float(percent_str.replace("%", ""))
            except ValueError:
                percent = 0.0

            self._notify(url, ProgressInfo(
                state=DownloadState.DOWNLOADING,
                percent=percent,
                speed=d.get("_speed_str", ""),
                eta=d.get("_eta_str", ""),
                downloaded_bytes=d.get("downloaded_bytes", 0),
                total_bytes=d.get("total_bytes") or d.get("total_bytes_estimate", 0),
                title=d.get("info_dict", {}).get("title", url) if d.get("info_dict") else url,
            ))

        elif status == "finished":
            info = d.get("info_dict") or {}
            self._notify(url, ProgressInfo(
                state=DownloadState.PROCESSING,
                title=info.get("title", url),
                percent=100.0,
            ))

    def _build_opts(
        self,
        save_path: str,
        format_spec: str,
        proxy: str,
        cookies_path: str,
        subtitle_langs: str,
        write_subtitles: bool,
        write_auto_subs: bool,
        embed_subtitles: bool,
        merge_output_format: str,
        js_runtimes: str,
        player_client: str,
        url: str,
    ) -> dict:
        """Build yt-dlp option dict."""
        opts: dict = {
            "outtmpl": f"{save_path}/%(title)s.%(ext)s",
            "format": format_spec,
            "merge_output_format": merge_output_format,
            "progress_hooks": [lambda d, u=url: self._progress_hook(u, d)],
            "no_warnings": False,
            "quiet": False,
            "noprogress": False,
        }

        # Proxy
        if proxy:
            opts["proxy"] = proxy

        # Cookies
        if cookies_path:
            opts["cookiefile"] = cookies_path

        # Subtitles
        if write_subtitles or write_auto_subs:
            opts["writesubtitles"] = write_subtitles
            opts["writeautomaticsub"] = write_auto_subs
            if subtitle_langs:
                opts["subtitleslangs"] = [lang.strip() for lang in subtitle_langs.split(",")]
            if embed_subtitles:
                opts["embedsubtitle"] = True

        # JS runtime
        if js_runtimes:
            opts["js_runtimes"] = js_runtimes

        # Player client
        if player_client and player_client != "web":
            clients = [c.strip() for c in player_client.split(",")]
            opts["extractor_args"] = {"youtube": {"player_client": clients}}

        return opts


# ─── Download manager (queue) ──────────────────────────────────────────────────

class DownloadManager:
    """Manages a sequential download queue with thread-safe state."""

    def __init__(self, downloader: Downloader):
        self._downloader = downloader
        self._queue: list[dict] = []
        self._current_index: int = -1
        self._lock = threading.Lock()
        self._worker: Optional[threading.Thread] = None
        self._running = False

    def add(self, task: dict) -> int:
        """Add a download task to the queue. Returns the task index."""
        with self._lock:
            self._queue.append(task)
            return len(self._queue) - 1

    def remove(self, index: int) -> None:
        """Remove a task from the queue by index."""
        with self._lock:
            if 0 <= index < len(self._queue):
                self._queue.pop(index)

    def get_queue(self) -> list[dict]:
        """Return a copy of the current queue."""
        with self._lock:
            return list(self._queue)

    def start(self) -> None:
        """Start processing the queue (sequential)."""
        if self._running:
            return
        self._running = True
        self._worker = threading.Thread(target=self._process_queue, daemon=True)
        self._worker.start()

    def cancel_current(self) -> None:
        """Cancel the current download."""
        self._downloader.cancel()

    def cancel_all(self) -> None:
        """Cancel current and clear remaining queue."""
        self._downloader.cancel()
        with self._lock:
            self._queue.clear()
        self._running = False

    def _process_queue(self) -> None:
        """Process tasks sequentially in the background."""
        while self._running:
            task = None
            with self._lock:
                self._current_index += 1
                if self._current_index < len(self._queue):
                    task = self._queue[self._current_index]

            if task is None:
                self._running = False
                break

            self._downloader.download(**task)

            # Remove finished/errored from queue consideration
            if self._downloader.is_cancelled:
                self._running = False
                break
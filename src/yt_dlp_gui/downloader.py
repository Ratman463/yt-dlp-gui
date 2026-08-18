"""
yt-dlp Python API wrapper for yt-dlp-gui.

- ``Downloader``: wraps a single yt-dlp download with progress callbacks,
  per-instance cancellation, and log routing.
- ``DownloadManager``: a sequential FIFO queue driven by one persistent
  worker thread. Each task gets its own ``Downloader`` instance, so
  cancelling one task never affects the others, and tasks submitted after
  the queue drains are still picked up.
"""

from __future__ import annotations

import logging
import re
import threading
import uuid
from collections import OrderedDict
from enum import Enum
from typing import Callable, Optional

import yt_dlp

logger = logging.getLogger(__name__)

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def _clean_str(value) -> str:
    """Strip ANSI escape codes and surrounding whitespace."""
    if not value:
        return ""
    return _ANSI_RE.sub("", str(value)).strip()


# ─── Download states ───────────────────────────────────────────────────────────

class DownloadState(Enum):
    """State machine for a download task."""
    QUEUED      = "queued"
    EXTRACTING  = "extracting"
    DOWNLOADING = "downloading"
    PROCESSING  = "processing"
    FINISHED    = "finished"
    ERROR       = "error"
    CANCELLED   = "cancelled"


# States in which a task is still expected to make progress.
ACTIVE_STATES = (
    DownloadState.QUEUED,
    DownloadState.EXTRACTING,
    DownloadState.DOWNLOADING,
    DownloadState.PROCESSING,
)


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


# ─── Log routing ───────────────────────────────────────────────────────────────

class _YtDlpLogger:
    """yt-dlp logger shim that forwards output lines to a callback."""

    def __init__(self, on_log: Callable[[str], None]):
        self._on_log = on_log

    def debug(self, msg):
        self._emit(msg)

    def info(self, msg):
        self._emit(msg)

    def warning(self, msg):
        self._emit(msg)

    def error(self, msg):
        self._emit(msg)

    def _emit(self, msg):
        line = str(msg).rstrip()
        if not line:
            return
        try:
            self._on_log(line)
        except Exception:
            logger.exception("Error in log callback")


# ─── Downloader (one per task) ─────────────────────────────────────────────────

class Downloader:
    """Wraps a single yt-dlp download with progress callbacks and cancellation.

    Each instance is independent: ``cancel()`` only affects the download run
    by *this* instance. The manager creates one per task.
    """

    def __init__(self, on_progress: Callable[[str, ProgressInfo], None]):
        """
        Args:
            on_progress: Callback receiving (url, ProgressInfo).
                         Called from a background thread — must be thread-safe.
        """
        self._on_progress = on_progress
        self._cancel_event = threading.Event()

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
        download_playlist: bool = False,
        on_log: Optional[Callable[[str], None]] = None,
    ) -> None:
        """Download a single video or playlist. Blocks until done (call from a worker thread)."""
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
            noplaylist=not download_playlist,
            on_log=on_log,
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
        """Signal this download to stop."""
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
            # Prefer computing percent from raw bytes — _percent_str is a
            # localized/colored display string and may not parse.
            downloaded = d.get("downloaded_bytes") or 0
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            if total:
                percent = min(downloaded * 100.0 / total, 100.0)
            else:
                try:
                    percent = float(_clean_str(d.get("_percent_str", "0%")).rstrip("%") or 0.0)
                except ValueError:
                    percent = 0.0

            self._notify(url, ProgressInfo(
                state=DownloadState.DOWNLOADING,
                percent=percent,
                speed=_clean_str(d.get("_speed_str", "")),
                eta=_clean_str(d.get("_eta_str", "")),
                downloaded_bytes=downloaded,
                total_bytes=total,
                title=(d.get("info_dict") or {}).get("title", url),
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
        noplaylist: bool = True,
        on_log: Optional[Callable[[str], None]] = None,
    ) -> dict:
        """Build yt-dlp option dict."""
        # Normalize separators so outtmpl is consistent on every platform.
        safe_path = (save_path or "").strip().replace("\\", "/").rstrip("/")

        opts: dict = {
            "outtmpl": f"{safe_path}/%(title)s.%(ext)s",
            "format": format_spec,
            "merge_output_format": merge_output_format,
            "noplaylist": noplaylist,
            "progress_hooks": [lambda d, u=url: self._progress_hook(u, d)],
            # All output goes to the logger shim instead of stderr.
            "quiet": True,
            "no_warnings": False,
            "noprogress": True,
            "logger": _YtDlpLogger(on_log or (lambda line: None)),
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
                opts["subtitleslangs"] = [lang.strip() for lang in subtitle_langs.split(",") if lang.strip()]
            if embed_subtitles:
                opts["embedsubtitle"] = True

        # JS runtime
        if js_runtimes:
            opts["js_runtimes"] = js_runtimes

        # Player client
        if player_client and player_client != "web":
            clients = [c.strip() for c in player_client.split(",") if c.strip()]
            opts["extractor_args"] = {"youtube": {"player_client": clients}}

        return opts


# ─── Download manager (queue) ──────────────────────────────────────────────────

class DownloadTask:
    """A queued download: stable id plus the downloader kwargs."""

    __slots__ = ("id", "params", "url")

    def __init__(self, task_id: str, params: dict):
        self.id = task_id
        self.params = dict(params)
        self.url = str(self.params.get("url", ""))


class DownloadManager:
    """Sequential download queue with per-task cancellation.

    Design notes (fixes the old index-based loop):

    - One *persistent* worker thread waits on a condition variable; tasks
      submitted after the queue drains are picked up immediately.
    - Pending tasks live in an insertion-ordered dict (FIFO). No indices,
      so the queue can be trimmed/cleared without desyncing anything.
    - Each task runs on its own ``Downloader`` instance → cancelling the
      current download never kills the rest of the queue.
    """

    def __init__(
        self,
        on_event: Callable[[str, str, ProgressInfo], None],
        on_log: Optional[Callable[[str, str], None]] = None,
        downloader_factory: Optional[Callable[..., "Downloader"]] = None,
    ):
        """
        Args:
            on_event: Callback ``(task_id, url, ProgressInfo)`` — may fire
                      from worker or caller threads; must be thread-safe.
            on_log:   Optional callback ``(task_id, line)`` for yt-dlp output.
            downloader_factory: Test seam; defaults to building a Downloader.
        """
        self._on_event = on_event
        self._on_log = on_log
        self._factory = downloader_factory or (lambda on_progress: Downloader(on_progress=on_progress))

        self._cond = threading.Condition()
        self._pending: "OrderedDict[str, DownloadTask]" = OrderedDict()
        self._current: Optional[tuple[DownloadTask, object]] = None
        self._stop = threading.Event()
        self._worker: Optional[threading.Thread] = None

    # ── Public API ────────────────────────────────────────────────────────────

    def submit(self, params: dict, task_id: Optional[str] = None) -> str:
        """Queue a download (kwargs for Downloader.download). Returns the task id."""
        task_id = task_id or uuid.uuid4().hex[:12]
        with self._cond:
            self._pending[task_id] = DownloadTask(task_id, params)
            self._cond.notify_all()
        self.start()
        return task_id

    def start(self) -> None:
        """Ensure the worker thread is running."""
        with self._cond:
            if self._worker is not None and self._worker.is_alive():
                return
            self._stop.clear()
            self._worker = threading.Thread(
                target=self._run, name="yt-dlp-gui-queue", daemon=True,
            )
            self._worker.start()

    def cancel(self, task_id: str) -> None:
        """Cancel one task: queued tasks are dropped, the current one is signalled."""
        with self._cond:
            task = self._pending.pop(task_id, None)
            if task is None:
                current = self._current
                if current is not None and current[0].id == task_id:
                    current[1].cancel()
                    # CANCELLED event is emitted by the downloader itself.
                return
        self._emit(task.id, task.url, ProgressInfo(
            state=DownloadState.CANCELLED, title=task.url,
        ))

    def cancel_all(self) -> None:
        """Cancel the current download and drop every queued task."""
        with self._cond:
            tasks = list(self._pending.values())
            self._pending.clear()
            current = self._current
        if current is not None:
            current[1].cancel()
        for task in tasks:
            self._emit(task.id, task.url, ProgressInfo(
                state=DownloadState.CANCELLED, title=task.url,
            ))

    def shutdown(self) -> None:
        """Stop the worker after the current download is cancelled. For app exit."""
        with self._cond:
            self._stop.set()
            self._pending.clear()
            current = self._current
            self._cond.notify_all()
        if current is not None:
            current[1].cancel()

    @property
    def pending_count(self) -> int:
        with self._cond:
            return len(self._pending)

    # ── Worker ─────────────────────────────────────────────────────────────────

    def _run(self) -> None:
        while True:
            with self._cond:
                while not self._pending and not self._stop.is_set():
                    self._cond.wait(0.5)
                if not self._pending:
                    return  # stop requested and nothing left
                _, task = self._pending.popitem(last=False)
                downloader = self._factory(
                    on_progress=lambda u, i, t=task: self._emit(t.id, u, i),
                )
                self._current = (task, downloader)

            try:
                params = dict(task.params)
                params.setdefault(
                    "on_log", lambda line, t=task: self._emit_log(t.id, line),
                )
                downloader.download(**params)
            except Exception as e:  # defensive: download() already catches
                logger.exception("Download task crashed")
                self._emit(task.id, task.url, ProgressInfo(
                    state=DownloadState.ERROR,
                    title=task.url,
                    error_message=f"Unexpected error: {e}",
                ))
            finally:
                with self._cond:
                    self._current = None

    # ── Event helpers ──────────────────────────────────────────────────────────

    def _emit(self, task_id: str, url: str, info: ProgressInfo) -> None:
        try:
            self._on_event(task_id, url, info)
        except Exception:
            logger.exception("Error in event callback")

    def _emit_log(self, task_id: str, line: str) -> None:
        if self._on_log is None:
            return
        try:
            self._on_log(task_id, line)
        except Exception:
            logger.exception("Error in log callback")

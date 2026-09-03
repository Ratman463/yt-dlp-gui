"""
yt-dlp Python API wrapper for yt-dlp-gui.

Layers
------

* ``Downloader`` wraps a single yt-dlp download with progress callbacks,
  per-instance cancellation, and log routing. One instance per task.
* ``DownloadManager`` is a sequential FIFO queue driven by one persistent
  worker thread. Each task gets its own ``Downloader`` instance, so
  cancelling one task never affects the others, and tasks submitted
  after the queue drains are still picked up.

Design choices (the previous version had bugs around all of these):

* The worker thread persists for the lifetime of the manager — it waits
  on a condition variable instead of dying when the queue is empty.
  Tasks submitted after a drain are picked up immediately.
* Pending tasks live in an insertion-ordered dict (FIFO). No indices, so
  trimming/clearing the queue can never desync anything.
* ``cancel(task_id)`` distinguishes queued vs running tasks: queued tasks
  are simply dropped; the running one has its ``Downloader`` signalled.
"""

from __future__ import annotations

import logging
import re
import threading
import uuid
from collections import OrderedDict
from enum import Enum
from typing import Any, Callable, Optional, Union

import yt_dlp

logger = logging.getLogger(__name__)

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def _clean_str(value: Any) -> str:
    """Strip ANSI escape codes and surrounding whitespace from *value*."""
    if value is None:
        return ""
    return _ANSI_RE.sub("", str(value)).strip()


# ─── Download states ───────────────────────────────────────────────────────────


class DownloadState(Enum):
    """State machine for a download task."""

    QUEUED = "queued"
    EXTRACTING = "extracting"
    DOWNLOADING = "downloading"
    PROCESSING = "processing"
    FINISHED = "finished"
    ERROR = "error"
    CANCELLED = "cancelled"


# States in which a task is still expected to make progress.
ACTIVE_STATES = (
    DownloadState.QUEUED,
    DownloadState.EXTRACTING,
    DownloadState.DOWNLOADING,
    DownloadState.PROCESSING,
)

# Terminal states — once reached, no further callbacks are expected.
TERMINAL_STATES = (
    DownloadState.FINISHED,
    DownloadState.ERROR,
    DownloadState.CANCELLED,
)


# ─── Progress info ─────────────────────────────────────────────────────────────


class ProgressInfo:
    """Structured progress data passed to UI callbacks."""

    __slots__ = (
        "state",
        "percent",
        "speed",
        "eta",
        "downloaded_bytes",
        "total_bytes",
        "title",
        "error_message",
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

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return (
            f"ProgressInfo(state={self.state.value!r}, percent={self.percent:.1f}, "
            f"title={self.title!r})"
        )


# ─── Log routing ───────────────────────────────────────────────────────────────


class _YtDlpLogger:
    """yt-dlp logger shim that forwards output lines to a callback.

    yt-dlp calls ``debug`` / ``info`` / ``warning`` / ``error`` with a
    single string argument. We forward each non-empty line verbatim.
    """

    def __init__(self, on_log: Callable[[str], None]):
        self._on_log = on_log

    def debug(self, msg: Any) -> None:
        self._emit(msg)

    def info(self, msg: Any) -> None:
        self._emit(msg)

    def warning(self, msg: Any) -> None:
        self._emit(msg)

    def error(self, msg: Any) -> None:
        self._emit(msg)

    def _emit(self, msg: Any) -> None:
        line = _clean_str(msg)
        if not line:
            return
        try:
            self._on_log(line)
        except Exception:
            logger.exception("Error in log callback")


# ─── Downloader (one per task) ─────────────────────────────────────────────────


class Downloader:
    """Wraps a single yt-dlp download with progress callbacks and cancellation.

    Each instance is independent: ``cancel()`` only affects the download
    run by *this* instance. The manager creates one per task so that
    cancelling the active download never kills the rest of the queue.
    """

    def __init__(self, on_progress: Callable[[str, ProgressInfo], None]):
        """
        Args:
            on_progress: Callback receiving ``(url, ProgressInfo)``. Called
                from a worker thread, so it must be thread-safe.
        """
        self._on_progress = on_progress
        self._cancel_event = threading.Event()

    # ── Public API ────────────────────────────────────────────────────────────

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
        js_runtimes: Union[str, dict] = {"node": {}},
        player_client: str = "web",
        download_playlist: bool = False,
        on_log: Optional[Callable[[str], None]] = None,
    ) -> None:
        """Download a single video or playlist.

        Blocks until the download finishes, errors out, or is cancelled.
        Intended to be called from a worker thread.
        """
        self._cancel_event.clear()
        self._notify(url, ProgressInfo(state=DownloadState.EXTRACTING, title=url))

        opts = self._build_opts(
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
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = (info or {}).get("title", url)
                self._notify(url, ProgressInfo(
                    state=DownloadState.PROCESSING, title=title,
                ))
                self._notify(url, ProgressInfo(
                    state=DownloadState.FINISHED,
                    title=title,
                    percent=100.0,
                ))
        except yt_dlp.utils.DownloadError as exc:
            if self._cancel_event.is_set():
                self._notify(url, ProgressInfo(
                    state=DownloadState.CANCELLED, title=url,
                ))
            else:
                self._notify(url, ProgressInfo(
                    state=DownloadState.ERROR,
                    title=url,
                    error_message=str(exc),
                ))
        except Exception as exc:  # defensive: yt-dlp should not raise here
            logger.exception("Unexpected download error")
            self._notify(url, ProgressInfo(
                state=DownloadState.ERROR,
                title=url,
                error_message=f"Unexpected error: {exc}",
            ))

    def cancel(self) -> None:
        """Signal this download to stop. Idempotent."""
        self._cancel_event.set()

    @property
    def is_cancelled(self) -> bool:
        return self._cancel_event.is_set()

    # ── Private ───────────────────────────────────────────────────────────────

    def _notify(self, url: str, info: ProgressInfo) -> None:
        """Thread-safe notification to the UI callback."""
        try:
            self._on_progress(url, info)
        except Exception:
            logger.exception("Error in progress callback")

    def _progress_hook(self, url: str, d: dict) -> None:
        """yt-dlp progress hook — converts raw dicts to ProgressInfo."""
        if self._cancel_event.is_set():
            # Raising here tells yt-dlp to abort the current download.
            raise yt_dlp.utils.DownloadError("Download cancelled by user")

        status = d.get("status", "")

        if status == "downloading":
            # Prefer computing percent from raw bytes — ``_percent_str`` is a
            # localized, ANSI-coloured display string and may not parse.
            downloaded = d.get("downloaded_bytes") or 0
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            if total:
                percent = min(downloaded * 100.0 / total, 100.0)
            else:
                try:
                    percent = float(
                        _clean_str(d.get("_percent_str", "0%")).rstrip("%") or 0.0
                    )
                except ValueError:
                    percent = 0.0

            info_dict = d.get("info_dict") or {}
            self._notify(url, ProgressInfo(
                state=DownloadState.DOWNLOADING,
                percent=percent,
                speed=_clean_str(d.get("_speed_str", "")),
                eta=_clean_str(d.get("_eta_str", "")),
                downloaded_bytes=downloaded,
                total_bytes=total,
                title=info_dict.get("title", url),
            ))

        elif status == "finished":
            info_dict = d.get("info_dict") or {}
            self._notify(url, ProgressInfo(
                state=DownloadState.PROCESSING,
                title=info_dict.get("title", url),
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
        js_runtimes: Union[str, dict],
        player_client: str,
        url: str,
        noplaylist: bool = True,
        on_log: Optional[Callable[[str], None]] = None,
    ) -> dict:
        """Build the yt-dlp option dict for one download."""
        # Normalize the path so outtmpl is consistent on every platform.
        safe_path = (save_path or "").strip().replace("\\", "/").rstrip("/")

        opts: dict[str, Any] = {
            "outtmpl": f"{safe_path}/%(title)s.%(ext)s",
            "format": format_spec,
            "merge_output_format": merge_output_format,
            "noplaylist": noplaylist,
            "progress_hooks": [lambda d, u=url: self._progress_hook(u, d)],
            # All output is routed to the logger shim, never raw stderr.
            "quiet": True,
            "no_warnings": False,
            "noprogress": True,
            "logger": _YtDlpLogger(on_log or (lambda line: None)),
        }

        # Proxy — only add when explicitly set.
        if proxy:
            opts["proxy"] = proxy

        # Cookies — only add when explicitly set.
        if cookies_path:
            opts["cookiefile"] = cookies_path

        # Subtitles.
        if write_subtitles or write_auto_subs:
            opts["writesubtitles"] = write_subtitles
            opts["writeautomaticsub"] = write_auto_subs
            if subtitle_langs:
                langs = [
                    lang.strip()
                    for lang in subtitle_langs.split(",")
                    if lang.strip()
                ]
                if langs:
                    opts["subtitleslangs"] = langs
            if embed_subtitles:
                opts["embedsubtitle"] = True

        # JS runtime — yt-dlp >= 2024.11 requires a dict like {"node": {}}.
        # Backwards-compat: accept a comma-separated string and convert it.
        if js_runtimes:
            if isinstance(js_runtimes, dict):
                opts["js_runtimes"] = js_runtimes
            elif isinstance(js_runtimes, str):
                runtimes = [r.strip() for r in js_runtimes.split(",") if r.strip()]
                if runtimes:
                    opts["js_runtimes"] = {name: {} for name in runtimes}

        # Player client — only emit extractor_args when not the default.
        if player_client and player_client != "web":
            clients = [c.strip() for c in player_client.split(",") if c.strip()]
            if clients:
                opts["extractor_args"] = {"youtube": {"player_client": clients}}

        return opts


# ─── Download manager (queue) ──────────────────────────────────────────────────


class DownloadTask:
    """A queued download: a stable id plus the downloader kwargs."""

    __slots__ = ("id", "params", "url")

    def __init__(self, task_id: str, params: dict):
        self.id = task_id
        self.params = dict(params)
        self.url = str(self.params.get("url", ""))


class DownloadManager:
    """Sequential download queue with per-task cancellation.

    The worker thread is created lazily by :meth:`start` and kept alive
    for the lifetime of the manager; it waits on a condition variable
    when there is nothing to do.
    """

    def __init__(
        self,
        on_event: Callable[[str, str, ProgressInfo], None],
        on_log: Optional[Callable[[str, str], None]] = None,
        downloader_factory: Optional[Callable[..., "Downloader"]] = None,
    ):
        """
        Args:
            on_event: Callback ``(task_id, url, ProgressInfo)``. May fire
                from the worker thread, so it must be thread-safe.
            on_log: Optional callback ``(task_id, line)`` for yt-dlp output.
            downloader_factory: Test seam; defaults to building a Downloader.
        """
        self._on_event = on_event
        self._on_log = on_log
        self._factory = downloader_factory or (
            lambda on_progress: Downloader(on_progress=on_progress)
        )

        self._cond = threading.Condition()
        self._pending: "OrderedDict[str, DownloadTask]" = OrderedDict()
        self._current: Optional[tuple[DownloadTask, object]] = None
        self._stop = threading.Event()
        self._worker: Optional[threading.Thread] = None

    # ── Public API ────────────────────────────────────────────────────────────

    def submit(self, params: dict, task_id: Optional[str] = None) -> str:
        """Queue a download (kwargs for ``Downloader.download``).

        Returns the task id. The worker thread is started if it isn't
        already running.
        """
        task_id = task_id or uuid.uuid4().hex[:12]
        with self._cond:
            self._pending[task_id] = DownloadTask(task_id, params)
            self._cond.notify_all()
        self.start()
        return task_id

    def start(self) -> None:
        """Ensure the worker thread is running (idempotent)."""
        with self._cond:
            if self._worker is not None and self._worker.is_alive():
                return
            self._stop.clear()
            self._worker = threading.Thread(
                target=self._run,
                name="yt-dlp-gui-queue",
                daemon=True,
            )
            self._worker.start()

    def cancel(self, task_id: str) -> None:
        """Cancel one task.

        * Queued tasks are dropped from the pending dict and a CANCELLED
          event is emitted immediately.
        * The currently running task has its Downloader signalled AND a
          CANCELLED event is emitted immediately so the UI updates without
          waiting for yt-dlp to observe the signal (which may never happen
          if the task is stuck in EXTRACTING on a bad URL).
        * Unknown ids are a no-op.
        """
        with self._cond:
            task = self._pending.pop(task_id, None)
            if task is not None:
                # Queued task — emit CANCELLED outside the lock.
                pass
            else:
                current = self._current
                if current is not None and current[0].id == task_id:
                    # Active task — signal the downloader AND emit CANCELLED
                    # immediately so the UI doesn't appear frozen while
                    # waiting for yt-dlp to abort.
                    current[1].cancel()
                    task = current[0]
                else:
                    return
        self._emit(task.id, task.url, ProgressInfo(
            state=DownloadState.CANCELLED, title=task.url,
        ))

    def cancel_all(self) -> None:
        """Cancel the current download and drop every queued task.

        Emits CANCELLED events for every task immediately, including the
        currently running one, so the UI reflects the stop without waiting
        for yt-dlp to abort.
        """
        with self._cond:
            tasks = list(self._pending.values())
            self._pending.clear()
            current = self._current
        if current is not None:
            current[1].cancel()
            tasks.append(current[0])
        for task in tasks:
            self._emit(task.id, task.url, ProgressInfo(
                state=DownloadState.CANCELLED, title=task.url,
            ))

    def shutdown(self) -> None:
        """Stop the worker after the current download is cancelled.

        Intended for application exit.
        """
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

    @property
    def current_task_id(self) -> Optional[str]:
        with self._cond:
            return self._current[0].id if self._current is not None else None

    # ── Worker ─────────────────────────────────────────────────────────────────

    def _run(self) -> None:
        """Main loop of the worker thread."""
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
            except Exception as exc:  # defensive: download() already catches
                logger.exception("Download task crashed")
                self._emit(task.id, task.url, ProgressInfo(
                    state=DownloadState.ERROR,
                    title=task.url,
                    error_message=f"Unexpected error: {exc}",
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

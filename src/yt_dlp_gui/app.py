"""
Main application window for yt-dlp-gui.

NEO_ESOTERIC_MONUMENT aesthetic: warm alabaster canvas, charcoal borders,
deep crimson etch lines, matte brass accents, strictly rectangular.
"""

from __future__ import annotations

import threading
import customtkinter as ctk
from tkinter import messagebox

from .theme import theme, CORNER_RADIUS, apply_theme
from .config import load_config, save_config
from .downloader import (
    DownloadManager,
    DownloadState,
    ProgressInfo,
    ACTIVE_STATES,
)
from .widgets import (
    MonumentFrame, MonumentScrollableFrame,
    BrassButton, EtchButton, DangerButton,
    MonumentLabel, MonumentCaption,
    DownloadItemWidget,
)
from .dialogs import AddDownloadDialog

# Keys copied straight from dialog params into the persisted config.
_CONFIG_FROM_PARAMS = {
    "save_path": "save_path",
    "proxy": "proxy",
    "cookies_path": "cookies_path",
    "subtitle_langs": "subtitle_langs",
    "write_subtitles": "write_subtitles",
    "write_auto_subs": "write_auto_subs",
    "embed_subtitles": "embed_subtitles",
    "player_client": "player_client",
    "download_playlist": "download_playlist",
    "format_spec": "format",
}


class YtDlpGuiApp(ctk.CTk):
    """Main application window — download list is the primary area."""

    def __init__(self):
        super().__init__()

        self._config = load_config()
        self._download_items: dict[str, DownloadItemWidget] = {}  # task_id -> widget
        self._task_params: dict[str, dict] = {}                    # task_id -> params
        self._last_log_pct: dict[str, float] = {}                  # log throttling

        # ─── Window config ──────────────────────────────────────────────
        self.title("YT-DLP-GUI")
        self.configure(fg_color=theme.bg_primary)
        self.geometry("800x600")
        self.minsize(640, 480)

        # ─── Manager setup ──────────────────────────────────────────────
        self._manager = DownloadManager(
            on_event=self._on_progress,
            on_log=self._on_log,
        )

        # ─── Build UI ────────────────────────────────────────────────────
        self._build_ui()

        # ─── Window close ───────────────────────────────────────────────
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ─── UI construction ───────────────────────────────────────────────────

    def _build_ui(self):
        """Construct the main window layout."""
        self.grid_rowconfigure(3, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # ─── Etch line at the very top — 3px crimson ────────────────────
        ctk.CTkFrame(self, height=3, fg_color=theme.accent_crimson, corner_radius=0
                     ).grid(row=0, column=0, sticky="ew")

        # ─── Header ─────────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        header.grid(row=1, column=0, sticky="ew", padx=0, pady=0)
        header.grid_columnconfigure(1, weight=1)

        # Title
        title_label = ctk.CTkLabel(
            header, text="YT-DLP-GUI",
            font=theme.font_h2, text_color=theme.text_primary,
        )
        title_label.grid(row=0, column=0, padx=(24, 8), pady=(14, 0), sticky="w")

        # Caption
        caption = MonumentCaption(header, text="MONUMENTAL VIDEO ARCHIVE")
        caption.grid(row=1, column=0, padx=(24, 0), pady=(0, 12), sticky="w")

        # Action buttons
        btn_frame = ctk.CTkFrame(header, fg_color="transparent", corner_radius=0)
        btn_frame.grid(row=0, column=1, rowspan=2, padx=(0, 24), pady=(14, 12), sticky="e")

        BrassButton(btn_frame, text="+ ADD", width=100, height=36,
                    command=self._open_add_dialog).pack(side="left", padx=(0, 8))

        DangerButton(btn_frame, text="✕ STOP ALL", width=100, height=36,
                     command=self._stop_all).pack(side="left")

        # ─── Divider ────────────────────────────────────────────────────
        ctk.CTkFrame(self, height=1, fg_color=theme.border_default, corner_radius=0
                     ).grid(row=2, column=0, sticky="ew")

        # ─── Download list (main area) ─────────────────────────────────
        list_frame = MonumentFrame(self, corner_radius=CORNER_RADIUS)
        list_frame.grid(row=3, column=0, sticky="nsew", padx=16, pady=(8, 8))
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)

        self._scrollable = MonumentScrollableFrame(list_frame)
        self._scrollable.grid(row=0, column=0, sticky="nsew", padx=1, pady=1)
        self._scrollable.grid_columnconfigure(0, weight=1)

        # Empty state
        self._empty_label = MonumentCaption(
            self._scrollable,
            text="NO DOWNLOADS — CLICK + ADD TO BEGIN",
        )
        self._empty_label.grid(row=0, column=0, pady=48)

        # ─── Footer — Log panel toggle ─────────────────────────────────
        footer = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0, height=32)
        footer.grid(row=4, column=0, sticky="ew", padx=16, pady=(0, 8))
        footer.grid_columnconfigure(1, weight=1)

        EtchButton(footer, text="▼ LOG", width=80, height=28,
                   command=self._toggle_log).grid(row=0, column=0)

        self._status_label = MonumentCaption(footer, text="READY")
        self._status_label.grid(row=0, column=1, sticky="e", padx=(0, 8))

        # ─── Log panel (hidden by default) ─────────────────────────────
        self._log_visible = False
        self._log_frame = MonumentFrame(self, corner_radius=CORNER_RADIUS)
        self._log_text = ctk.CTkTextbox(
            self._log_frame, corner_radius=CORNER_RADIUS, height=130,
            fg_color=theme.bg_card, text_color=theme.text_secondary,
            font=theme.font_body_sm, wrap="word",
        )
        self._log_text.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        self._log_frame.grid_columnconfigure(0, weight=1)
        self._log_frame.grid_rowconfigure(0, weight=1)

    # ─── Actions ────────────────────────────────────────────────────────────

    def _open_add_dialog(self):
        """Open the Add Download dialog."""
        dialog = AddDownloadDialog(self, self._config, on_submit=self._add_download)
        self.wait_window(dialog)

    def _add_download(self, params: dict):
        """Add a download task to the queue and start it."""
        url = params.get("url", "").strip()
        if not url:
            return

        # Validate / backfill the save path — an empty outtmpl would write
        # straight to the filesystem root.
        save_path = (params.get("save_path") or "").strip() or self._config.get("save_path", "")
        if not save_path:
            messagebox.showerror(
                "Missing save path",
                "No download folder is set. Please choose one in the add dialog.",
            )
            return
        params["save_path"] = save_path

        # Persist the full set of preferences for next time.
        for src_key, cfg_key in _CONFIG_FROM_PARAMS.items():
            if src_key in params:
                self._config[cfg_key] = params[src_key]
        save_config(self._config)

        # Hide empty state
        self._empty_label.grid_remove()

        # Queue the task first so it gets a stable id...
        task_id = self._manager.submit(params)
        self._task_params[task_id] = params

        # ...then build its row.
        item = DownloadItemWidget(
            self._scrollable, task_id, url,
            on_cancel=self._cancel_download,
            on_retry=self._retry_download,
        )
        self._download_items[task_id] = item
        item.grid(sticky="ew", padx=4, pady=2)

        self._update_status()

    def _cancel_download(self, task_id: str):
        """Cancel a specific task (queued or current)."""
        self._manager.cancel(task_id)

    def _retry_download(self, task_id: str):
        """Retry a failed or cancelled task by re-submitting its params."""
        params = self._task_params.get(task_id)
        if params is None:
            return
        # Drop the old row; _add_download creates a fresh task.
        item = self._download_items.pop(task_id, None)
        if item is not None:
            item.destroy()
        self._task_params.pop(task_id, None)
        self._last_log_pct.pop(task_id, None)
        self._add_download(dict(params))

    def _stop_all(self):
        """Cancel all downloads."""
        self._manager.cancel_all()
        self._update_status()

    def _toggle_log(self):
        """Toggle the log panel visibility."""
        self._log_visible = not self._log_visible
        if self._log_visible:
            self._log_frame.grid(row=5, column=0, sticky="ew", padx=16, pady=(0, 8))
        else:
            self._log_frame.grid_forget()

    # ─── Status ──────────────────────────────────────────────────────────────

    def _update_status(self):
        """Recompute the status caption from current widget states."""
        states = [w.state for w in self._download_items.values()]
        active = sum(1 for s in states if s in ACTIVE_STATES)
        errors = sum(1 for s in states if s == DownloadState.ERROR)
        cancelled = sum(1 for s in states if s == DownloadState.CANCELLED)
        finished = sum(1 for s in states if s == DownloadState.FINISHED)

        if active > 0:
            text = f"DOWNLOADING — {active} ACTIVE"
        elif errors > 0:
            text = "ERROR — CHECK LOG"
        elif cancelled > 0 and finished == 0:
            text = "STOPPED"
        elif states:
            text = "ALL DOWNLOADS COMPLETE"
        else:
            text = "READY"
        self._status_label.configure(text=text)

    # ─── Callbacks (thread-safe scheduling) ──────────────────────────────────

    def _on_progress(self, task_id: str, url: str, info: ProgressInfo):
        """Called from manager threads — schedule UI update on main thread."""
        try:
            self.after(0, self._update_item, task_id, info)
        except Exception:
            # Window is being destroyed — drop the event instead of
            # crashing the worker thread.
            pass

    def _on_log(self, task_id: str, line: str):
        """Called from downloader threads — schedule log append on main thread."""
        try:
            self.after(0, self._log, f"[#{task_id[:4]}] {line}")
        except Exception:
            pass

    def _update_item(self, task_id: str, info: ProgressInfo):
        """Update a download item widget on the main thread."""
        # Log — throttle the per-percent spam to one line every 5%.
        if info.state == DownloadState.ERROR:
            self._log(f"[#{task_id[:4]}][ERROR] {info.error_message}")
        elif info.state == DownloadState.FINISHED:
            self._log(f"[#{task_id[:4]}][DONE] {info.title}")
        elif info.state == DownloadState.DOWNLOADING:
            last = self._last_log_pct.get(task_id, -100.0)
            if abs(info.percent - last) >= 5.0:
                speed = f" {info.speed}" if info.speed else ""
                eta = f" ETA {info.eta}" if info.eta else ""
                self._log(f"[#{task_id[:4]}] {info.percent:5.1f}%{speed}{eta}")
                self._last_log_pct[task_id] = info.percent

        # Trim the error caption to its first line (full text is in the log).
        if info.state == DownloadState.ERROR:
            full = (info.error_message or "Unknown error").strip()
            first_line = full.splitlines()[0][:220] if full else "Unknown error"
            info = ProgressInfo(
                state=DownloadState.ERROR,
                title=info.title,
                error_message=first_line,
            )

        # Update widget
        item = self._download_items.get(task_id)
        if item is not None:
            item.update_progress(info)

        if info.state in (DownloadState.FINISHED, DownloadState.ERROR, DownloadState.CANCELLED):
            self._last_log_pct.pop(task_id, None)
            self._update_status()

    def _log(self, message: str):
        """Append a message to the log panel."""
        self._log_text.insert("end", message + "\n")
        self._log_text.see("end")

    # ─── Cleanup ────────────────────────────────────────────────────────────

    def _on_close(self):
        """Handle window close — cancel downloads and exit."""
        self._manager.shutdown()
        self.destroy()


def main():
    """Entry point for yt-dlp-gui."""
    apply_theme()
    app = YtDlpGuiApp()
    app.mainloop()


if __name__ == "__main__":
    main()

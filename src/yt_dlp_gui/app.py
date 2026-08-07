"""
Main application window for yt-dlp-gui.

NEO_ESOTERIC_MONUMENT aesthetic: warm alabaster canvas, charcoal borders,
deep crimson etch lines, matte brass accents, strictly rectangular.
"""

from __future__ import annotations

import os
import threading
import customtkinter as ctk
from tkinter import messagebox

from .theme import theme, CORNER_RADIUS, apply_theme
from .config import load_config, save_config
from .downloader import Downloader, DownloadManager, DownloadState, ProgressInfo
from .widgets import (
    MonumentFrame, MonumentScrollableFrame,
    BrassButton, EtchButton, DangerButton,
    MonumentLabel, MonumentCaption,
    DownloadItemWidget,
)
from .dialogs import AddDownloadDialog


class YtDlpGuiApp(ctk.CTk):
    """Main application window — download list is the primary area."""

    def __init__(self):
        super().__init__()

        self._config = load_config()
        self._download_items: dict[str, DownloadItemWidget] = {}
        self._task_params: dict[str, dict] = {}  # url -> params for retry

        # ─── Window config ──────────────────────────────────────────────
        self.title("YT-DLP-GUI")
        self.configure(fg_color=theme.bg_primary)
        self.geometry("800x600")
        self.minsize(640, 480)

        # ─── Downloader setup ───────────────────────────────────────────
        self._downloader = Downloader(on_progress=self._on_progress)
        self._manager = DownloadManager(self._downloader)

        # ─── Build UI ────────────────────────────────────────────────────
        self._build_ui()

        # ─── Window close ───────────────────────────────────────────────
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ─── UI construction ───────────────────────────────────────────────────

    def _build_ui(self):
        """Construct the main window layout."""
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # ─── Header ─────────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0, height=60)
        header.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        header.grid_columnconfigure(1, weight=1)

        # Etch line at the very top — 3px crimson
        ctk.CTkFrame(self, height=3, fg_color=theme.accent_crimson, corner_radius=0
                     ).grid(row=0, column=0, sticky="new")

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
                     ).grid(row=0, column=0, sticky="ew", pady=(57, 0))

        # ─── Download list (main area) ─────────────────────────────────
        list_frame = MonumentFrame(self, corner_radius=CORNER_RADIUS)
        list_frame.grid(row=1, column=0, sticky="nsew", padx=16, pady=(8, 8))
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
        footer.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 8))
        footer.grid_columnconfigure(1, weight=1)

        EtchButton(footer, text="▼ LOG", width=80, height=28,
                   command=self._toggle_log).grid(row=0, column=0)

        self._status_label = MonumentCaption(footer, text="READY")
        self._status_label.grid(row=0, column=1, sticky="e", padx=(0, 8))

        # ─── Log panel (hidden by default) ─────────────────────────────
        self._log_visible = False
        self._log_frame = MonumentFrame(self, corner_radius=CORNER_RADIUS, height=150)
        self._log_text = ctk.CTkTextbox(
            self._log_frame, corner_radius=CORNER_RADIUS,
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

        # Save relevant settings for next time
        self._config["save_path"] = params.get("save_path", self._config["save_path"])
        self._config["proxy"] = params.get("proxy", "")
        self._config["cookies_path"] = params.get("cookies_path", "")
        self._config["subtitle_langs"] = params.get("subtitle_langs", "")
        save_config(self._config)

        # Hide empty state
        self._empty_label.grid_remove()

        # Store params for retry
        self._task_params[url] = params

        # Create download item widget
        item = DownloadItemWidget(
            self._scrollable, url,
            on_cancel=self._cancel_download,
            on_retry=self._retry_download,
        )
        self._download_items[url] = item
        item.grid(sticky="ew", padx=4, pady=2)

        # Start download in background
        self._manager.add(params)
        self._manager.start()
        self._status_label.configure(text=f"DOWNLOADING — {len(self._download_items)} IN QUEUE")

    def _cancel_download(self, url: str):
        """Cancel a specific download."""
        self._manager.cancel_current()
        if url in self._download_items:
            item = self._download_items[url]
            item.update_progress(ProgressInfo(state=DownloadState.CANCELLED, title=url))

    def _retry_download(self, url: str):
        """Retry a failed download."""
        if url in self._task_params:
            params = self._task_params[url]
            # Remove old widget
            if url in self._download_items:
                self._download_items[url].destroy()
                del self._download_items[url]
            # Re-add
            self._add_download(params)

    def _stop_all(self):
        """Cancel all downloads."""
        self._manager.cancel_all()
        self._status_label.configure(text="STOPPED")

    def _toggle_log(self):
        """Toggle the log panel visibility."""
        self._log_visible = not self._log_visible
        if self._log_visible:
            self._log_frame.grid(row=3, column=0, sticky="ew", padx=16, pady=(0, 8))
        else:
            self._log_frame.grid_forget()

    # ─── Progress callback (thread-safe) ───────────────────────────────────

    def _on_progress(self, url: str, info: ProgressInfo):
        """Called from downloader thread — schedule UI update on main thread."""
        self.after(0, self._update_item, url, info)

    def _update_item(self, url: str, info: ProgressInfo):
        """Update a download item widget on the main thread."""
        # Log
        if info.state == DownloadState.ERROR:
            self._log(f"[ERROR] {url}: {info.error_message}")
        elif info.state == DownloadState.FINISHED:
            self._log(f"[DONE] {info.title}")
        elif info.state == DownloadState.DOWNLOADING:
            self._log(f"[{info.percent:.1f}%] {info.speed} ETA {info.eta}")

        # Update widget
        if url in self._download_items:
            self._download_items[url].update_progress(info)

        # Update status bar
        if info.state == DownloadState.FINISHED:
            active = sum(1 for w in self._download_items.values()
                        if w._state in (DownloadState.EXTRACTING, DownloadState.DOWNLOADING, DownloadState.PROCESSING, DownloadState.QUEUED))
            if active > 0:
                self._status_label.configure(text=f"REMAINING — {active} IN QUEUE")
            else:
                self._status_label.configure(text="ALL DOWNLOADS COMPLETE")
        elif info.state == DownloadState.ERROR:
            self._status_label.configure(text="ERROR — CHECK LOG")

    def _log(self, message: str):
        """Append a message to the log panel."""
        self._log_text.insert("end", message + "\n")
        self._log_text.see("end")

    # ─── Cleanup ────────────────────────────────────────────────────────────

    def _on_close(self):
        """Handle window close — cancel downloads and exit."""
        self._manager.cancel_all()
        self.destroy()


def main():
    """Entry point for yt-dlp-gui."""
    apply_theme()
    app = YtDlpGuiApp()
    app.mainloop()


if __name__ == "__main__":
    main()
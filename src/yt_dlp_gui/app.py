"""
Main application window for yt-dlp-gui.

SOFT_CARD "rounded card" aesthetic — lavender-mist canvas, white pill-
cornered cards, violet filled buttons, and generous breathing room.
Friendly, young, and uncluttered.

Layout
------

* Header — large title, subtitle, "+ 添加" and "全部停止" actions.
* Download list — scrollable, one :class:`DownloadItemWidget` per task.
* Footer — log toggle button and a status caption.
* Log panel — collapsible, hidden by default.
"""

from __future__ import annotations

import customtkinter as ctk
from tkinter import messagebox

from .theme import theme, CORNER_RADIUS, apply_theme
from . import icons
from .config import load_config, save_config
from .downloader import (
    DownloadManager,
    DownloadState,
    ProgressInfo,
    ACTIVE_STATES,
)
from .widgets import (
    MonumentFrame,
    MonumentScrollableFrame,
    BrassButton,
    EtchButton,
    DangerButton,
    MonumentCaption,
    DownloadItemWidget,
)
from .dialogs import AddDownloadDialog

# Keys copied straight from the dialog params into the persisted config.
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
    """Main application window — the download list is the primary area."""

    def __init__(self):
        super().__init__()

        self._config = load_config()
        self._download_items: dict[str, DownloadItemWidget] = {}  # task_id -> widget
        self._task_params: dict[str, dict] = {}  # task_id -> params
        self._last_log_pct: dict[str, float] = {}  # log throttling

        # ─── Window config ──────────────────────────────────────────────
        self.title("YT-DLP-GUI")
        self.configure(fg_color=theme.bg_primary)
        self.geometry("880x640")
        self.minsize(680, 500)

        # ─── Manager setup ──────────────────────────────────────────────
        self._manager = DownloadManager(
            on_event=self._on_progress,
            on_log=self._on_log,
        )

        # ─── UI ─────────────────────────────────────────────────────────
        self._build_ui()

        # ─── Window close ───────────────────────────────────────────────
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ─── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        """Construct the main window layout."""
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # ─── Header ────────────────────────────────────────────────────
        # Large title on the left, pill action buttons on the right —
        # floating freely on the mist canvas, no etch bar.
        header = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        header.grid(row=0, column=0, sticky="ew", padx=28, pady=(24, 0))
        header.grid_columnconfigure(0, weight=1)

        # Large title block.
        title_block = ctk.CTkFrame(header, fg_color="transparent", corner_radius=0)
        title_block.grid(row=0, column=0, sticky="w")
        title_block.grid_columnconfigure(0, weight=0)

        ctk.CTkLabel(
            title_block,
            text="下载",
            font=theme.font_large_title,
            text_color=theme.text_primary,
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        MonumentCaption(
            title_block, text="用 yt-dlp 下载视频与播放列表"
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

        # Action buttons — rounded chips on the right.
        btn_frame = ctk.CTkFrame(header, fg_color="transparent", corner_radius=0)
        btn_frame.grid(row=0, column=1, sticky="e")

        # "+ 添加" — primary filled violet pill.
        self._add_btn = BrassButton(
            btn_frame, text="+  添加", width=104, height=36,
            command=self._open_add_dialog,
        )
        self._add_btn.pack(side="left", padx=(0, 10))

        # "全部停止" — soft rose chip (destructive but gentle).
        self._stop_btn = DangerButton(
            btn_frame, text="全部停止", width=104, height=36,
            command=self._stop_all,
            fg_color=theme.error_container,
            hover_color=theme.error_container_hover,
            text_color=theme.accent_red,
        )
        self._stop_btn.pack(side="left")

        # ─── Download list ─────────────────────────────────────────────
        # Cards float on the canvas — no separator line, just breathing
        # room between the header and the list.
        list_container = ctk.CTkFrame(
            self, fg_color="transparent", corner_radius=0,
        )
        list_container.grid(row=2, column=0, sticky="nsew", padx=28, pady=(18, 10))
        list_container.grid_rowconfigure(0, weight=1)
        list_container.grid_columnconfigure(0, weight=1)

        self._scrollable = MonumentScrollableFrame(list_container)
        self._scrollable.grid(row=0, column=0, sticky="nsew")
        self._scrollable.grid_columnconfigure(0, weight=1)

        # Empty state — centered caption.
        self._empty_label = ctk.CTkLabel(
            self._scrollable,
            text="暂无下载任务",
            font=theme.font_title_3,
            text_color=theme.text_tertiary,
        )
        self._empty_label.grid(row=0, column=0, pady=(96, 6))

        self._empty_hint = MonumentCaption(
            self._scrollable,
            text="点击右上角「+ 添加」开始下载",
        )
        self._empty_hint.grid(row=1, column=0, pady=(0, 96))

        # ─── Footer ────────────────────────────────────────────────────
        footer = ctk.CTkFrame(
            self, fg_color="transparent", corner_radius=0, height=36,
        )
        footer.grid(row=3, column=0, sticky="ew", padx=28, pady=(0, 16))
        footer.grid_columnconfigure(1, weight=1)

        # Log toggle — sky chip with a lucide chevron that flips on expand.
        self._log_btn = EtchButton(
            footer, text="日志", width=92, height=30,
            image=icons.chevron_down_blue(),
            command=self._toggle_log,
        )
        self._log_btn.grid(row=0, column=0)

        # Status caption on the right.
        self._status_label = MonumentCaption(footer, text="就绪")
        self._status_label.grid(row=0, column=1, sticky="e", padx=(0, 8))

        # ─── Log panel ─────────────────────────────────────────────────
        # Hidden by default — toggled by the footer button.
        self._log_visible = False
        self._log_frame = ctk.CTkFrame(
            self, fg_color=theme.bg_card, corner_radius=CORNER_RADIUS,
            border_width=1, border_color=theme.border_default,
        )
        self._log_text = ctk.CTkTextbox(
            self._log_frame,
            corner_radius=CORNER_RADIUS,
            height=150,
            fg_color="transparent",
            text_color=theme.text_secondary,
            font=theme.font_body_sm,
            wrap="word",
        )
        self._log_text.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        self._log_frame.grid_columnconfigure(0, weight=1)
        self._log_frame.grid_rowconfigure(0, weight=1)

    # ─── Actions ────────────────────────────────────────────────────────────

    def _open_add_dialog(self):
        """Open the Add Download dialog and wait for it to close."""
        dialog = AddDownloadDialog(self, self._config, on_submit=self._add_download)
        self.wait_window(dialog)

    def _add_download(self, params: dict):
        """Add a download task to the queue and start it."""
        url = (params.get("url") or "").strip()
        if not url:
            return

        # Backfill / validate the save path — an empty outtmpl would write
        # straight to the filesystem root.
        save_path = (params.get("save_path") or "").strip() or self._config.get(
            "save_path", ""
        )
        if not save_path:
            messagebox.showerror(
                "缺少保存路径",
                "尚未设置下载文件夹，请在添加对话框中选择一个。",
            )
            return
        params["save_path"] = save_path

        # Persist preferences for next launch.
        for src_key, cfg_key in _CONFIG_FROM_PARAMS.items():
            if src_key in params:
                self._config[cfg_key] = params[src_key]
        save_config(self._config)

        # Hide empty state.
        self._empty_label.grid_remove()
        self._empty_hint.grid_remove()

        # Queue the task first so it gets a stable id...
        task_id = self._manager.submit(params)
        self._task_params[task_id] = params

        # ...then build its row.
        item = DownloadItemWidget(
            self._scrollable,
            task_id,
            url,
            on_cancel=self._cancel_download,
            on_retry=self._retry_download,
        )
        self._download_items[task_id] = item
        item.grid(sticky="ew", padx=2, pady=6)

        self._update_status()

    def _cancel_download(self, task_id: str):
        self._manager.cancel(task_id)

    def _retry_download(self, task_id: str):
        """Retry a failed/cancelled task by re-submitting its params."""
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
        self._manager.cancel_all()
        self._update_status()

    def _toggle_log(self):
        self._log_visible = not self._log_visible
        if self._log_visible:
            self._log_frame.grid(row=4, column=0, sticky="ew", padx=28, pady=(0, 16))
            self._log_btn.configure(
                image=icons.chevron_up_blue(), text="日志",
            )
        else:
            self._log_frame.grid_forget()
            self._log_btn.configure(
                image=icons.chevron_down_blue(), text="日志",
            )

    # ─── Status ──────────────────────────────────────────────────────────────

    def _update_status(self):
        """Recompute the status caption from the current widget states."""
        states = [w.state for w in self._download_items.values()]
        active = sum(1 for s in states if s in ACTIVE_STATES)
        errors = sum(1 for s in states if s == DownloadState.ERROR)
        cancelled = sum(1 for s in states if s == DownloadState.CANCELLED)
        finished = sum(1 for s in states if s == DownloadState.FINISHED)

        if active > 0:
            text = f"正在下载 · {active} 个任务"
        elif errors > 0:
            text = f"有 {errors} 个任务出错"
        elif cancelled > 0 and finished == 0:
            text = "已停止"
        elif states:
            text = "全部下载完成"
        else:
            text = "就绪"
        self._status_label.configure(text=text)

    # ─── Callbacks (thread-safe scheduling) ──────────────────────────────────

    def _on_progress(self, task_id: str, url: str, info: ProgressInfo):
        """Called from worker threads — schedule the UI update on main."""
        try:
            self.after(0, self._update_item, task_id, info)
        except Exception:
            # Window is being destroyed — drop the event instead of
            # crashing the worker.
            pass

    def _on_log(self, task_id: str, line: str):
        """Called from downloader threads — schedule a log append on main."""
        try:
            self.after(0, self._log, f"[#{task_id[:4]}] {line}")
        except Exception:
            pass

    def _update_item(self, task_id: str, info: ProgressInfo):
        """Update a download item widget on the main thread."""
        # Log — throttle the per-percent spam to one line every 5%.
        if info.state == DownloadState.ERROR:
            self._log(f"[#{task_id[:4]}][错误] {info.error_message}")
        elif info.state == DownloadState.FINISHED:
            self._log(f"[#{task_id[:4]}][完成] {info.title}")
        elif info.state == DownloadState.DOWNLOADING:
            last = self._last_log_pct.get(task_id, -100.0)
            if abs(info.percent - last) >= 5.0:
                speed = f" {info.speed}" if info.speed else ""
                eta = f" ETA {info.eta}" if info.eta else ""
                self._log(f"[#{task_id[:4]}] {info.percent:5.1f}%{speed}{eta}")
                self._last_log_pct[task_id] = info.percent

        # Trim the error caption to its first line (full text is in the log).
        if info.state == DownloadState.ERROR:
            full = (info.error_message or "未知错误").strip()
            first_line = full.splitlines()[0][:220] if full else "未知错误"
            info = ProgressInfo(
                state=DownloadState.ERROR,
                title=info.title,
                error_message=first_line,
            )

        item = self._download_items.get(task_id)
        if item is not None:
            item.update_progress(info)

        if info.state in (
            DownloadState.FINISHED,
            DownloadState.ERROR,
            DownloadState.CANCELLED,
        ):
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

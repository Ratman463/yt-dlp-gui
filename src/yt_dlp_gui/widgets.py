"""
Custom widgets for yt-dlp-gui following the NEO_ESOTERIC_MONUMENT design system.

Strictly rectangular (0px radius), warm alabaster canvas, charcoal borders,
matte brass accents, and deep crimson etch lines for depth.
"""

from __future__ import annotations

import customtkinter as ctk

from .theme import theme, CORNER_RADIUS


# ─── Base styled frame ────────────────────────────────────────────────────────

class MonumentFrame(ctk.CTkFrame):
    """Base frame with 0px corners and alabaster background."""

    def __init__(self, master, **kwargs):
        kwargs.setdefault("corner_radius", CORNER_RADIUS)
        kwargs.setdefault("fg_color", theme.bg_card)
        kwargs.setdefault("border_color", theme.border_default)
        kwargs.setdefault("border_width", 1)
        super().__init__(master, **kwargs)


class MonumentScrollableFrame(ctk.CTkScrollableFrame):
    """Scrollable frame with 0px corners and alabaster background."""

    def __init__(self, master, **kwargs):
        kwargs.setdefault("corner_radius", CORNER_RADIUS)
        kwargs.setdefault("fg_color", theme.bg_card)
        kwargs.setdefault("border_color", theme.border_default)
        kwargs.setdefault("border_width", 1)
        super().__init__(master, **kwargs)


# ─── Buttons ───────────────────────────────────────────────────────────────────

class BrassButton(ctk.CTkButton):
    """Primary action button — Matte Brass background with charcoal text."""

    def __init__(self, master, text="Action", command=None, **kwargs):
        kwargs.setdefault("text", text)
        kwargs.setdefault("command", command)
        kwargs.setdefault("corner_radius", CORNER_RADIUS)
        kwargs.setdefault("fg_color", theme.accent_brass)
        kwargs.setdefault("hover_color", theme.accent_crimson)
        kwargs.setdefault("text_color", theme.text_primary)
        kwargs.setdefault("font", theme.font_label)
        kwargs.setdefault("border_width", 0)
        super().__init__(master, **kwargs)


class EtchButton(ctk.CTkButton):
    """Secondary action button — Charcoal border, crimson hover (the Etch)."""

    def __init__(self, master, text="Action", command=None, **kwargs):
        kwargs.setdefault("text", text)
        kwargs.setdefault("command", command)
        kwargs.setdefault("corner_radius", CORNER_RADIUS)
        kwargs.setdefault("fg_color", theme.bg_card)
        kwargs.setdefault("hover_color", theme.bg_hover)
        kwargs.setdefault("text_color", theme.text_primary)
        kwargs.setdefault("font", theme.font_label)
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("border_color", theme.border_strong)
        super().__init__(master, **kwargs)


class DangerButton(ctk.CTkButton):
    """Destructive action button — Deep Crimson background."""

    def __init__(self, master, text="Cancel", command=None, **kwargs):
        kwargs.setdefault("text", text)
        kwargs.setdefault("command", command)
        kwargs.setdefault("corner_radius", CORNER_RADIUS)
        kwargs.setdefault("fg_color", theme.error_text)
        kwargs.setdefault("hover_color", "#8b1515")
        kwargs.setdefault("text_color", theme.text_on_brass)
        kwargs.setdefault("font", theme.font_label)
        kwargs.setdefault("border_width", 0)
        super().__init__(master, **kwargs)


# ─── Input fields ──────────────────────────────────────────────────────────────

class MonumentEntry(ctk.CTkEntry):
    """Text input with 0px corners, bottom-border emphasis on focus."""

    def __init__(self, master, placeholder="", **kwargs):
        kwargs.setdefault("placeholder_text", placeholder)
        kwargs.setdefault("corner_radius", CORNER_RADIUS)
        kwargs.setdefault("fg_color", theme.bg_input)
        kwargs.setdefault("border_color", theme.border_default)
        kwargs.setdefault("text_color", theme.text_primary)
        kwargs.setdefault("font", theme.font_body)
        kwargs.setdefault("border_width", 1)
        super().__init__(master, **kwargs)


class MonumentLabel(ctk.CTkLabel):
    """Label in the body font."""

    def __init__(self, master, text="", **kwargs):
        kwargs.setdefault("text", text)
        kwargs.setdefault("text_color", theme.text_primary)
        kwargs.setdefault("font", theme.font_body)
        super().__init__(master, **kwargs)


class MonumentCaption(ctk.CTkLabel):
    """Small caption/metadata label in label-caps style."""

    def __init__(self, master, text="", **kwargs):
        kwargs.setdefault("text", text)
        kwargs.setdefault("text_color", theme.text_secondary)
        kwargs.setdefault("font", theme.font_label_sm)
        super().__init__(master, **kwargs)


# ─── Download list item ───────────────────────────────────────────────────────

from .downloader import DownloadState, ACTIVE_STATES


class DownloadItemWidget(MonumentFrame):
    """A single row in the download list, showing title, progress, state, and actions.

    Identified by a stable task_id; displays the URL until a title is known.
    """

    def __init__(self, master, task_id: str, url: str,
                 on_cancel=None, on_retry=None, **kwargs):
        super().__init__(master, **kwargs)

        self._task_id = task_id
        self._url = url
        self._on_cancel = on_cancel
        self._on_retry = on_retry
        self._state = DownloadState.QUEUED

        # ─── Inner layout: title row + progress row ───
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=0)

        # State indicator — a thin 3px vertical crimson line on the left (the Etch)
        self._state_indicator = ctk.CTkFrame(
            self, width=3, corner_radius=0,
            fg_color=theme.border_default,
        )
        self._state_indicator.grid(row=0, column=0, rowspan=2, sticky="ns", padx=(0, 0), pady=8)

        # Title
        self._title_label = MonumentCaption(self, text=url, anchor="w")
        self._title_label.grid(row=0, column=1, sticky="ew", padx=(12, 8), pady=(8, 2))

        # Right side: state label + actions
        self._state_label = MonumentCaption(self, text="排队中", anchor="e")
        self._state_label.grid(row=0, column=2, sticky="e", padx=(0, 8), pady=(8, 2))

        # Progress bar
        self._progress = ctk.CTkProgressBar(self, corner_radius=0, fg_color=theme.border_default)
        self._progress.grid(row=1, column=1, sticky="ew", padx=(12, 8), pady=(2, 4))
        self._progress.set(0)

        # Speed / ETA
        self._speed_label = MonumentCaption(self, text="", anchor="e")
        self._speed_label.grid(row=1, column=2, sticky="e", padx=(0, 8), pady=(2, 4))

        # Error message (hidden by default)
        self._error_label = MonumentCaption(self, text="", anchor="w", wraplength=400)
        self._error_label.grid(row=2, column=1, columnspan=2, sticky="ew", padx=(12, 8), pady=(0, 4))
        self._error_label.grid_remove()

        # Action buttons (hidden by default)
        self._btn_frame = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self._btn_frame.grid(row=2, column=2, sticky="e", padx=(0, 8), pady=(0, 4))
        self._btn_frame.grid_remove()

        self._cancel_btn = EtchButton(self._btn_frame, text="✕", width=28, height=28,
                                       command=self._handle_cancel)
        self._cancel_btn.pack(side="left", padx=(0, 4))

        self._retry_btn = EtchButton(self._btn_frame, text="↻", width=28, height=28,
                                      command=self._handle_retry)

        self._update_state_display()

    # ─── Public API ────────────────────────────────────────────────────────────

    @property
    def task_id(self) -> str:
        return self._task_id

    @property
    def url(self) -> str:
        return self._url

    @property
    def state(self) -> DownloadState:
        return self._state

    def update_progress(self, info) -> None:
        """Update display based on ProgressInfo from the downloader."""
        self._state = info.state
        self._update_state_display()

        if info.title and info.title != self._url:
            self._title_label.configure(text=info.title)

        if info.state == DownloadState.DOWNLOADING:
            self._progress.set(max(0.0, min(info.percent / 100.0, 1.0)))
            speed_text = f"{info.speed} | ETA {info.eta}" if info.speed else ""
            self._speed_label.configure(text=speed_text)
            self._state_label.configure(text=f"{info.percent:.1f}%")

        elif info.state == DownloadState.EXTRACTING:
            self._progress.set(0)
            self._state_label.configure(text="解析中")

        elif info.state == DownloadState.PROCESSING:
            self._progress.set(1.0)
            self._state_label.configure(text="处理中")

        elif info.state == DownloadState.FINISHED:
            self._progress.set(1.0)
            self._state_label.configure(text="✓ 完成")
            self._speed_label.configure(text="")

        elif info.state == DownloadState.ERROR:
            self._state_label.configure(text="✗ 出错")
            self._error_label.configure(text=info.error_message)
            self._speed_label.configure(text="")

        elif info.state == DownloadState.CANCELLED:
            self._state_label.configure(text="已取消")
            self._speed_label.configure(text="")

    # ─── Private ───────────────────────────────────────────────────────────────

    def _update_state_display(self) -> None:
        """Update the state indicator color and visible action buttons."""
        color_map = {
            DownloadState.QUEUED: theme.border_default,
            DownloadState.EXTRACTING: theme.accent_brass,
            DownloadState.DOWNLOADING: theme.accent_brass,
            DownloadState.PROCESSING: theme.accent_brass,
            DownloadState.FINISHED: theme.accent_success,
            DownloadState.ERROR: theme.error_text,
            DownloadState.CANCELLED: theme.text_secondary,
        }
        self._state_indicator.configure(fg_color=color_map.get(self._state, theme.border_default))

        if self._state in ACTIVE_STATES:
            # Active (including queued) → cancellable, retry hidden.
            self._error_label.grid_remove()
            self._btn_frame.grid()
            self._cancel_btn.pack(side="left", padx=(0, 4))
            self._retry_btn.pack_forget()
        elif self._state in (DownloadState.ERROR, DownloadState.CANCELLED):
            # Terminal-but-recoverable → retry only.
            if self._state == DownloadState.ERROR:
                self._error_label.grid()
            else:
                self._error_label.grid_remove()
            self._btn_frame.grid()
            self._cancel_btn.pack_forget()
            self._retry_btn.pack(side="left")
        else:  # FINISHED
            self._btn_frame.grid_remove()
            self._error_label.grid_remove()

    def _handle_cancel(self):
        if self._on_cancel:
            self._on_cancel(self._task_id)

    def _handle_retry(self):
        if self._on_retry:
            self._on_retry(self._task_id)
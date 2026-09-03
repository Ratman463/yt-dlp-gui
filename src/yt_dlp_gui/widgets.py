"""
Custom widgets for yt-dlp-gui in the SOFT_CARD "rounded card" style.

Pill buttons, pastel chips, white cards with hairline borders, and tube
progress tracks on a cool mist canvas. Friendly and young — depth comes
from surface contrast, never shadows. Small glyphs use lucide icons
pre-rendered to transparent PNGs (see :mod:`yt_dlp_gui.icons`).
"""

from __future__ import annotations

import customtkinter as ctk

from . import icons
from .theme import theme, CORNER_RADIUS, CORNER_RADIUS_PILL


# ─── Base styled frames ────────────────────────────────────────────────────────


class MonumentFrame(ctk.CTkFrame):
    """Soft card frame — white fill, 16px corners, hairline border.

    Name kept for backward compatibility with tests / imports; semantics
    are now rounded-card, not Monument.
    """

    def __init__(self, master, **kwargs):
        kwargs.setdefault("corner_radius", CORNER_RADIUS)
        kwargs.setdefault("fg_color", theme.bg_card)
        # Hairline border makes the card read as a floating tile on the
        # mist canvas even when two cards touch.
        kwargs.setdefault("border_color", theme.border_default)
        kwargs.setdefault("border_width", 1)
        super().__init__(master, **kwargs)


class MonumentScrollableFrame(ctk.CTkScrollableFrame):
    """Scrollable frame — transparent, cards provide their own surface."""

    def __init__(self, master, **kwargs):
        kwargs.setdefault("corner_radius", CORNER_RADIUS)
        # Transparent background — the parent card provides the surface.
        kwargs.setdefault("fg_color", "transparent")
        kwargs.setdefault("border_color", theme.border_default)
        kwargs.setdefault("border_width", 0)
        super().__init__(master, **kwargs)


# ─── Buttons ───────────────────────────────────────────────────────────────────


class BrassButton(ctk.CTkButton):
    """Primary action button — filled violet pill.

    Name kept for backward compatibility with tests / imports.
    """

    def __init__(self, master, text="Action", command=None, **kwargs):
        kwargs.setdefault("text", text)
        kwargs.setdefault("command", command)
        # Pill shape — CTk clamps the radius to half the button height.
        kwargs.setdefault("corner_radius", CORNER_RADIUS_PILL)
        kwargs.setdefault("fg_color", theme.accent_blue)
        kwargs.setdefault("hover_color", theme.accent_blue_hover)
        kwargs.setdefault("text_color", theme.text_on_accent)
        kwargs.setdefault("font", theme.font_headline)
        kwargs.setdefault("border_width", 0)
        super().__init__(master, **kwargs)


class EtchButton(ctk.CTkButton):
    """Secondary button — soft lilac chip with violet text.

    The pastel fill reads as friendly and tappable, unlike a bare text
    link. Hover deepens the lilac slightly.
    """

    def __init__(self, master, text="Action", command=None, **kwargs):
        kwargs.setdefault("text", text)
        kwargs.setdefault("command", command)
        kwargs.setdefault("corner_radius", CORNER_RADIUS_PILL)
        kwargs.setdefault("fg_color", theme.primary_container)
        kwargs.setdefault("hover_color", theme.primary_container_hover)
        kwargs.setdefault("text_color", theme.accent_blue)
        kwargs.setdefault("font", theme.font_headline)
        kwargs.setdefault("border_width", 0)
        super().__init__(master, **kwargs)


class DangerButton(ctk.CTkButton):
    """Destructive button — filled rose pill by default.

    Callers can pass ``fg_color=theme.error_container`` and
    ``text_color=theme.accent_red`` for a soft rose chip (used by
    "全部停止" and other gentle destructive actions).
    """

    def __init__(self, master, text="Cancel", command=None, **kwargs):
        kwargs.setdefault("text", text)
        kwargs.setdefault("command", command)
        kwargs.setdefault("corner_radius", CORNER_RADIUS_PILL)
        kwargs.setdefault("fg_color", theme.accent_red)
        kwargs.setdefault("hover_color", theme.accent_red_hover)
        kwargs.setdefault("text_color", theme.text_on_accent)
        kwargs.setdefault("font", theme.font_headline)
        kwargs.setdefault("border_width", 0)
        super().__init__(master, **kwargs)


# ─── Inputs ─────────────────────────────────────────────────────────────────────


class MonumentEntry(ctk.CTkEntry):
    """Text input — soft gray well, 12px corners, hairline border.

    Name kept for backward compatibility.
    """

    def __init__(self, master, placeholder="", **kwargs):
        kwargs.setdefault("placeholder_text", placeholder)
        kwargs.setdefault("corner_radius", CORNER_RADIUS)
        # Inputs sit as soft wells on white cards — a light gray fill
        # distinguishes them from the card surface.
        kwargs.setdefault("fg_color", theme.bg_secondary)
        kwargs.setdefault("border_color", theme.border_default)
        kwargs.setdefault("text_color", theme.text_primary)
        kwargs.setdefault("placeholder_text_color", theme.text_tertiary)
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
    """Small caption — 12pt slate text for metadata and hints."""

    def __init__(self, master, text="", **kwargs):
        kwargs.setdefault("text", text)
        kwargs.setdefault("text_color", theme.text_secondary)
        kwargs.setdefault("font", theme.font_body_sm)
        super().__init__(master, **kwargs)


# ─── Option menu with lucide chevron ──────────────────────────────────────────


class IconOptionMenu(ctk.CTkOptionMenu):
    """CTkOptionMenu with the built-in triangle arrow replaced by a lucide
    chevron-down icon.

    The stock arrow is a canvas line item tagged ``dropdown_arrow`` that
    CTk redraws on every ``_draw()`` — so we remove it after every
    super()._draw() call and keep a transparent CTkLabel (holding the
    icon) positioned over the button area instead. Clicks on the icon
    label are forwarded so the dropdown still opens.
    """

    def __init__(self, master, icon=None, **kwargs):
        super().__init__(master, **kwargs)
        self._chevron_icon = icon if icon is not None else icons.chevron_down_slate()
        iw, ih = self._chevron_icon._size

        self._chevron_label = ctk.CTkLabel(
            self, text="", image=self._chevron_icon,
            fg_color="transparent", corner_radius=0,
        )
        # Clicks land on the label — forward them to the menu handler.
        self._chevron_label.bind("<Button-1>", self._clicked)
        self.bind("<Configure>", lambda _e: self._place_chevron())
        self._place_chevron()

    def _place_chevron(self):
        """Center the chevron on the right button area (width - height/2)."""
        if not self.winfo_exists():
            return
        w, h = self.winfo_width(), self.winfo_height()
        if w <= 1 or h <= 1:
            return
        iw, ih = self._chevron_icon._size
        cx = w - h // 2
        self._chevron_label.place(
            x=cx - iw // 2, y=(h - ih) // 2, width=iw, height=ih,
        )

    def _draw(self, no_color_updates=False):
        super()._draw(no_color_updates)
        # Remove the stock triangle — redraws recreate it, so delete here.
        try:
            self._canvas.delete("dropdown_arrow")
        except Exception:
            pass


# ─── Download list item ───────────────────────────────────────────────────────

from .downloader import DownloadState, ACTIVE_STATES  # noqa: E402


class DownloadItemWidget(MonumentFrame):
    """A single row in the download list.

    Rounded white card with the title, a tube progress track, status
    text, speed/ETA, and circular cancel / retry chips. Identified by a
    stable ``task_id`` so the app can route progress callbacks to it.
    """

    def __init__(
        self,
        master,
        task_id: str,
        url: str,
        on_cancel=None,
        on_retry=None,
        **kwargs,
    ):
        super().__init__(master, **kwargs)

        self._task_id = task_id
        self._url = url
        self._on_cancel = on_cancel
        self._on_retry = on_retry
        self._state = DownloadState.QUEUED

        # White tile with a hairline border, floating on the mist canvas.
        self.configure(fg_color=theme.bg_card, border_width=1)

        # Inner layout — state indicator | title + progress | actions.
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=0)

        # Status dot — a soft 10px colored circle in the upper-left.
        self._state_dot = ctk.CTkLabel(
            self, text="\u25cf", width=16,
            font=(theme.font_body_sm[0], 15, "normal"),
            text_color=theme.text_tertiary,
        )
        self._state_dot.grid(row=0, column=0, padx=(16, 8), pady=(14, 0), sticky="nw")

        # Title — shows the URL until the downloader reports a real title.
        self._title_label = ctk.CTkLabel(
            self, text=url, anchor="w",
            font=theme.font_headline,
            text_color=theme.text_primary,
        )
        self._title_label.grid(
            row=0, column=1, sticky="ew", padx=(4, 16), pady=(14, 2),
        )

        # State label (right side).
        self._state_label = MonumentCaption(self, text="排队中", anchor="e")
        self._state_label.grid(
            row=0, column=2, sticky="e", padx=(0, 16), pady=(14, 2),
        )

        # Progress bar — tube track, violet fill, rounded ends.
        self._progress = ctk.CTkProgressBar(
            self,
            corner_radius=CORNER_RADIUS_PILL,
            height=8,
            fg_color=theme.border_default,
            progress_color=theme.accent_blue,
        )
        self._progress.grid(row=1, column=1, sticky="ew", padx=(4, 16), pady=(4, 14))
        self._progress.set(0)

        # Speed / ETA (right side, below state).
        self._speed_label = MonumentCaption(self, text="", anchor="e")
        self._speed_label.grid(row=1, column=2, sticky="e", padx=(0, 16), pady=(4, 14))

        # Error message — hidden by default.
        self._error_label = MonumentCaption(self, text="", anchor="w", wraplength=400)
        self._error_label.configure(text_color=theme.accent_red)
        self._error_label.grid(
            row=2, column=1, columnspan=2, sticky="ew", padx=(4, 16), pady=(0, 14),
        )
        self._error_label.grid_remove()

        # Action buttons — hidden by default; 28px chips render as circles.
        self._btn_frame = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self._btn_frame.grid(row=2, column=2, sticky="e", padx=(0, 14), pady=(0, 14))
        self._btn_frame.grid_remove()

        self._cancel_btn = EtchButton(
            self._btn_frame, text="\u2715", width=28, height=28,
            command=self._handle_cancel,
        )
        self._cancel_btn.configure(
            fg_color=theme.chip_neutral,
            hover_color=theme.chip_neutral_hover,
            text_color=theme.text_secondary,
        )
        self._cancel_btn.pack(side="left", padx=(0, 6))

        self._retry_btn = EtchButton(
            self._btn_frame, text="\u21bb", width=28, height=28,
            command=self._handle_retry,
        )

        self._update_state_display()

    # ── Public API ────────────────────────────────────────────────────────────

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
        """Update the display based on a :class:`ProgressInfo`."""
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
            self._state_label.configure(text="\u2713 完成")
            self._speed_label.configure(text="")

        elif info.state == DownloadState.ERROR:
            self._state_label.configure(text="\u2717 出错")
            self._error_label.configure(text=info.error_message)
            self._speed_label.configure(text="")

        elif info.state == DownloadState.CANCELLED:
            self._state_label.configure(text="已取消")
            self._speed_label.configure(text="")

    # ── Private ───────────────────────────────────────────────────────────────

    def _update_state_display(self) -> None:
        """Update the status dot color and visible action buttons."""
        color_map = {
            DownloadState.QUEUED: theme.text_tertiary,
            DownloadState.EXTRACTING: theme.accent_orange,
            DownloadState.DOWNLOADING: theme.accent_blue,
            DownloadState.PROCESSING: theme.accent_blue,
            DownloadState.FINISHED: theme.accent_green,
            DownloadState.ERROR: theme.accent_red,
            DownloadState.CANCELLED: theme.text_tertiary,
        }
        self._state_dot.configure(
            text_color=color_map.get(self._state, theme.text_tertiary),
        )

        # Progress bar color follows state too.
        progress_color_map = {
            DownloadState.FINISHED: theme.accent_green,
            DownloadState.ERROR: theme.accent_red,
            DownloadState.CANCELLED: theme.text_tertiary,
        }
        self._progress.configure(
            progress_color=progress_color_map.get(self._state, theme.accent_blue),
        )

        if self._state in ACTIVE_STATES:
            # Active (including queued) — cancellable, retry hidden.
            self._error_label.grid_remove()
            self._btn_frame.grid()
            self._cancel_btn.pack(side="left", padx=(0, 4))
            self._retry_btn.pack_forget()
        elif self._state in (DownloadState.ERROR, DownloadState.CANCELLED):
            # Recoverable — retry only.
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

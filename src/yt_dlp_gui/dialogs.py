"""
Add-download dialog for yt-dlp-gui.

Single-page popup with all parameters laid out flat:
URL, format, subtitles, proxy, cookies, save path, playlist.

SOFT_CARD "rounded card" style — lavender-mist canvas around one large
white card holding the form, pill action buttons in the footer.
"""

from __future__ import annotations

import os

import customtkinter as ctk
from tkinter import filedialog, messagebox

from .theme import theme, CORNER_RADIUS, CORNER_RADIUS_SM
from .config import (
    FORMAT_PRESETS,
    CUSTOM_FORMAT_LABEL,
    DEFAULT_FORMAT_PRESET,
)
from . import icons
from .widgets import (
    BrassButton,
    EtchButton,
    IconOptionMenu,
    MonumentCaption,
)


class AddDownloadDialog(ctk.CTkToplevel):
    """Popup dialog for adding a new download task."""

    def __init__(self, master, config: dict, on_submit=None):
        super().__init__(master)

        self._config = config
        self._on_submit = on_submit
        self._result: dict | None = None

        # ─── Window config ─────────────────────────────────────────────────
        self.title("新建下载")
        self.configure(fg_color=theme.bg_primary)
        self.geometry("560x680")
        self.resizable(False, False)

        # Modal plumbing.
        self.transient(master)
        self.lift()
        self.focus_force()
        # Esc dismisses the dialog (same as the window close button).
        self.bind("<Escape>", lambda _e: self._on_cancel())
        # Take the modal grab only after the window is mapped — calling
        # grab_set() on a not-yet-viewable window raises TclError.
        self.after(150, self._safe_grab)

        # ─── Layout grid ───────────────────────────────────────────────────
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)
        # Column weight stretches the content/footer to the window width.
        self.grid_columnconfigure(0, weight=1)

        # ─── Header ────────────────────────────────────────────────────────
        # Transparent band on the mist canvas — title floats above the card.
        header = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text="新建下载",
            font=theme.font_title_2,
            text_color=theme.text_primary,
            anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=24, pady=(18, 4))

        MonumentCaption(
            header, text="输入视频链接并选择下载选项"
        ).grid(row=1, column=0, sticky="w", padx=24, pady=(0, 12))

        # ─── Scrollable content ────────────────────────────────────────────
        # One large white card holds the whole form.
        content = ctk.CTkScrollableFrame(
            self,
            corner_radius=CORNER_RADIUS,
            fg_color=theme.bg_card,
            border_width=1,
            border_color=theme.border_default,
        )
        content.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 14))
        content.grid_columnconfigure(0, weight=1)

        self._build_url_section(content)
        self._build_format_section(content)
        self._build_subtitle_section(content)
        self._build_proxy_section(content)
        self._build_cookies_section(content)
        self._build_path_section(content)
        self._build_playlist_section(content)
        self._build_footer()

    # ─── Section builders ──────────────────────────────────────────────────────

    _SECTION_ROWS = []  # filled in below to keep row counters in one place

    def _next_row(self) -> int:
        # Section headers consume two rows (label + spacer); each section
        # asks for the next free row via this helper so the builders can
        # be reordered without re-numbering everything.
        self._row_cursor = getattr(self, "_row_cursor", -1) + 1
        return self._row_cursor

    def _add_section_header(self, parent, text: str) -> int:
        """Add a soft section caption label above grouped controls.

        Small semibold slate text — no underline, no dots. Returns the
        row index of the *content* row (header_row + 1), so callers can
        place their widgets without bookkeeping.
        """
        header_row = self._next_row()
        ctk.CTkLabel(
            parent,
            text=text.upper(),
            font=theme.font_caption_bold,
            text_color=theme.text_secondary,
            anchor="w",
        ).grid(row=header_row, column=0, sticky="w", padx=16, pady=(14, 6))

        return self._next_row()

    # ── URL ──────────────────────────────────────────────────────────────────
    def _build_url_section(self, content):
        row = self._add_section_header(content, "链接（URL）")
        self._url_entry = ctk.CTkEntry(
            content,
            placeholder_text="https://www.youtube.com/watch?v=...",
            corner_radius=CORNER_RADIUS_SM,
            fg_color=theme.bg_secondary,
            border_color=theme.border_default,
            text_color=theme.text_primary,
            placeholder_text_color=theme.text_tertiary,
            font=theme.font_body,
            border_width=1,
            height=40,
        )
        self._url_entry.grid(row=row, column=0, sticky="ew", padx=16, pady=(0, 6))

    # ── Format ───────────────────────────────────────────────────────────────
    def _build_format_section(self, content):
        row = self._add_section_header(content, "画质格式")

        saved_format = self._config.get("format")
        initial_label = CUSTOM_FORMAT_LABEL
        for label, spec in FORMAT_PRESETS:
            if spec == saved_format:
                initial_label = label
                break
        else:
            initial_label = DEFAULT_FORMAT_PRESET

        self._format_var = ctk.StringVar(value=initial_label)
        self._format_menu = IconOptionMenu(
            content,
            icon=icons.chevron_down_slate(),
            values=[p[0] for p in FORMAT_PRESETS],
            variable=self._format_var,
            command=self._on_format_change,
            corner_radius=CORNER_RADIUS_SM,
            fg_color=theme.bg_secondary,
            button_color=theme.bg_secondary,
            button_hover_color=theme.bg_hover,
            text_color=theme.text_primary,
            dropdown_fg_color=theme.bg_card,
            font=theme.font_body,
        )
        self._format_menu.grid(row=row, column=0, sticky="ew", padx=16, pady=(0, 6))

        # Custom format entry — hidden unless the custom preset is selected.
        self._custom_format_entry = ctk.CTkEntry(
            content,
            placeholder_text="自定义格式串（如 bv[height<=720]+ba/best）",
            corner_radius=CORNER_RADIUS_SM,
            fg_color=theme.bg_secondary,
            border_color=theme.border_default,
            text_color=theme.text_primary,
            placeholder_text_color=theme.text_tertiary,
            font=theme.font_body,
            border_width=1,
            height=36,
        )
        custom_row = self._next_row()
        self._custom_format_entry.grid(
            row=custom_row, column=0, sticky="ew", padx=16, pady=(0, 6),
        )
        self._custom_format_entry.grid_remove()
        if initial_label == CUSTOM_FORMAT_LABEL:
            self._custom_format_entry.grid()
            if saved_format:
                self._custom_format_entry.insert(0, saved_format)

    # ── Subtitles ────────────────────────────────────────────────────────────
    def _build_subtitle_section(self, content):
        row = self._add_section_header(content, "字幕")

        self._write_subs_var = ctk.BooleanVar(
            value=bool(self._config.get("write_subtitles", True)),
        )
        self._write_auto_var = ctk.BooleanVar(
            value=bool(self._config.get("write_auto_subs", True)),
        )
        self._embed_subs_var = ctk.BooleanVar(
            value=bool(self._config.get("embed_subtitles", True)),
        )

        chk_frame = ctk.CTkFrame(content, fg_color="transparent", corner_radius=0)
        chk_frame.grid(row=row, column=0, sticky="ew", padx=16, pady=(0, 8))
        for i, (text, var) in enumerate([
            ("下载字幕", self._write_subs_var),
            ("含自动生成", self._write_auto_var),
            ("嵌入视频", self._embed_subs_var),
        ]):
            ctk.CTkCheckBox(
                chk_frame,
                text=text,
                variable=var,
                corner_radius=8,
                border_width=2,
                fg_color=theme.accent_blue,
                hover_color=theme.accent_blue_hover,
                border_color=theme.border_strong,
                text_color=theme.text_primary,
                font=theme.font_body_sm,
            ).grid(row=0, column=i, padx=(0, 16))

        lang_row = self._next_row()
        self._subs_lang_entry = ctk.CTkEntry(
            content,
            placeholder_text="zh-Hans,zh-Hant,en,ja",
            corner_radius=CORNER_RADIUS_SM,
            fg_color=theme.bg_secondary,
            border_color=theme.border_default,
            text_color=theme.text_primary,
            placeholder_text_color=theme.text_tertiary,
            font=theme.font_body,
            border_width=1,
            height=36,
        )
        self._subs_lang_entry.grid(
            row=lang_row, column=0, sticky="ew", padx=16, pady=(0, 6),
        )
        self._subs_lang_entry.insert(
            0, self._config.get("subtitle_langs", "zh-Hans,zh-Hant,en,ja"),
        )

    # ── Proxy ────────────────────────────────────────────────────────────────
    def _build_proxy_section(self, content):
        row = self._add_section_header(content, "代理")
        self._proxy_entry = ctk.CTkEntry(
            content,
            placeholder_text="http://127.0.0.1:7897（留空则直连）",
            corner_radius=CORNER_RADIUS_SM,
            fg_color=theme.bg_secondary,
            border_color=theme.border_default,
            text_color=theme.text_primary,
            placeholder_text_color=theme.text_tertiary,
            font=theme.font_body,
            border_width=1,
            height=36,
        )
        self._proxy_entry.grid(row=row, column=0, sticky="ew", padx=16, pady=(0, 6))
        if self._config.get("proxy"):
            self._proxy_entry.insert(0, self._config["proxy"])

    # ── Cookies ──────────────────────────────────────────────────────────────
    def _build_cookies_section(self, content):
        row = self._add_section_header(content, "Cookies")
        cookies_frame = ctk.CTkFrame(content, fg_color="transparent", corner_radius=0)
        cookies_frame.grid(row=row, column=0, sticky="ew", padx=16, pady=(0, 6))
        cookies_frame.grid_columnconfigure(0, weight=1)

        self._cookies_entry = ctk.CTkEntry(
            cookies_frame,
            placeholder_text="cookies.txt 文件路径",
            corner_radius=CORNER_RADIUS_SM,
            fg_color=theme.bg_secondary,
            border_color=theme.border_default,
            text_color=theme.text_primary,
            placeholder_text_color=theme.text_tertiary,
            font=theme.font_body,
            border_width=1,
            height=36,
        )
        self._cookies_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        if self._config.get("cookies_path"):
            self._cookies_entry.insert(0, self._config["cookies_path"])

        EtchButton(
            cookies_frame, text="", width=84, height=36,
            image=icons.browse_icon(),
            command=self._browse_cookies,
        ).grid(row=0, column=1)

    # ── Save path ────────────────────────────────────────────────────────────
    def _build_path_section(self, content):
        row = self._add_section_header(content, "保存到")
        path_frame = ctk.CTkFrame(content, fg_color="transparent", corner_radius=0)
        path_frame.grid(row=row, column=0, sticky="ew", padx=16, pady=(0, 6))
        path_frame.grid_columnconfigure(0, weight=1)

        self._path_entry = ctk.CTkEntry(
            path_frame,
            corner_radius=CORNER_RADIUS_SM,
            fg_color=theme.bg_secondary,
            border_color=theme.border_default,
            text_color=theme.text_primary,
            font=theme.font_body,
            border_width=1,
            height=36,
        )
        self._path_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self._path_entry.insert(
            0,
            self._config.get(
                "save_path", os.path.expanduser("~/Downloads"),
            ),
        )

        EtchButton(
            path_frame, text="", width=84, height=36,
            image=icons.browse_icon(),
            command=self._browse_path,
        ).grid(row=0, column=1)

    # ── Playlist ─────────────────────────────────────────────────────────────
    def _build_playlist_section(self, content):
        row = self._add_section_header(content, "播放列表")
        self._playlist_var = ctk.BooleanVar(
            value=bool(self._config.get("download_playlist", False)),
        )
        ctk.CTkCheckBox(
            content,
            text="下载整个播放列表（不勾选则只下载单个视频）",
            variable=self._playlist_var,
            corner_radius=8,
            border_width=2,
            fg_color=theme.accent_blue,
            hover_color=theme.accent_blue_hover,
            border_color=theme.border_strong,
            text_color=theme.text_primary,
            font=theme.font_body_sm,
        ).grid(row=row, column=0, sticky="w", padx=16, pady=(0, 14))

    # ── Footer ───────────────────────────────────────────────────────────────
    def _build_footer(self):
        footer = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0, height=60)
        footer.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 20))
        footer.grid_columnconfigure(0, weight=1)

        # No explicit cancel button — the window close (X) and Esc both
        # dismiss the dialog, so a duplicate 取消 chip was redundant.
        BrassButton(
            footer, text="添加到队列", width=160, height=40,
            command=self._on_submit_click,
        ).grid(row=0, column=0, sticky="e")

    # ─── Helpers ────────────────────────────────────────────────────────────────

    def _safe_grab(self):
        """Take the modal grab once the window is (probably) viewable."""
        try:
            if self.winfo_exists():
                self.grab_set()
        except Exception:
            # Window was closed before the grab fired — nothing to do.
            pass

    def _on_format_change(self, value: str):
        """Show/hide the custom format entry based on the preset selection."""
        if value == CUSTOM_FORMAT_LABEL:
            self._custom_format_entry.grid()
            self._custom_format_entry.focus_set()
        else:
            self._custom_format_entry.grid_remove()

    def _browse_cookies(self):
        path = filedialog.askopenfilename(
            title="选择 cookies 文件",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
        )
        if path:
            self._cookies_entry.delete(0, "end")
            self._cookies_entry.insert(0, path)

    def _browse_path(self):
        path = filedialog.askdirectory(title="选择下载文件夹")
        if path:
            self._path_entry.delete(0, "end")
            self._path_entry.insert(0, path)

    def _gather_result(self) -> dict | None:
        """Validate the form and return the params dict, or None on failure."""
        url = self._url_entry.get().strip()
        if not url:
            messagebox.showwarning("缺少链接", "请先输入视频链接。", parent=self)
            self._url_entry.focus_set()
            return None

        save_path = self._path_entry.get().strip()
        if not save_path:
            messagebox.showwarning("缺少保存路径", "请选择下载文件夹。", parent=self)
            return None

        # Resolve format — preset map or custom string.
        preset_map = dict(FORMAT_PRESETS)
        selected_label = self._format_var.get()
        if selected_label == CUSTOM_FORMAT_LABEL:
            format_spec = self._custom_format_entry.get().strip()
            if not format_spec:
                format_spec = "bv[height<=1080]+ba/b[height<=1080]/best"
        else:
            format_spec = preset_map.get(selected_label, preset_map[DEFAULT_FORMAT_PRESET])

        # Resolve player client (kept as default "web" — UI removed).
        player_client = "web"

        return {
            "url": url,
            "save_path": save_path,
            "format_spec": format_spec,
            "proxy": self._proxy_entry.get().strip(),
            "cookies_path": self._cookies_entry.get().strip(),
            "subtitle_langs": self._subs_lang_entry.get().strip(),
            "write_subtitles": self._write_subs_var.get(),
            "write_auto_subs": self._write_auto_var.get(),
            "embed_subtitles": self._embed_subs_var.get(),
            "merge_output_format": "mp4",
            # yt-dlp >= 2024.11 requires dict form {"node": {}}.
            "js_runtimes": {"node": {}},
            "player_client": player_client,
            "download_playlist": self._playlist_var.get(),
        }

    def _on_submit_click(self):
        """Gather parameters, fire the submit callback, and close the dialog."""
        result = self._gather_result()
        if result is None:
            return
        self._result = result
        if self._on_submit:
            self._on_submit(self._result)
        self._grab_release_safe()
        self.destroy()

    def _on_cancel(self):
        self._result = None
        self._grab_release_safe()
        self.destroy()

    def _grab_release_safe(self):
        try:
            self.grab_release()
        except Exception:
            pass

    @property
    def result(self) -> dict | None:
        return self._result

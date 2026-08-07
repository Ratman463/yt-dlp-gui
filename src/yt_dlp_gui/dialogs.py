"""
Add-download dialog for yt-dlp-gui.

Single-page popup with all parameters flat-laid:
URL, format, subtitles, proxy, cookies, save path.
Strictly rectangular, alabaster canvas, brass primary actions.
"""

from __future__ import annotations

import os
import customtkinter as ctk
from tkinter import filedialog

from .theme import theme, CORNER_RADIUS
from .config import FORMAT_PRESETS, PLAYER_CLIENT_OPTIONS


class AddDownloadDialog(ctk.CTkToplevel):
    """Popup dialog for adding a new download task."""

    def __init__(self, master, config: dict, on_submit=None):
        super().__init__(master)

        self._config = config
        self._on_submit = on_submit
        self._result: dict | None = None

        # ─── Window config ─────────────────────────────────────────────────
        self.title("ADD DOWNLOAD")
        self.configure(fg_color=theme.bg_primary)
        self.geometry("520x640")
        self.resizable(False, False)
        self.grab_set()  # modal

        # Center on parent
        self.transient(master)

        # ─── Main container ────────────────────────────────────────────────
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)

        # Header — Etch line (3px crimson top border)
        header = ctk.CTkFrame(self, fg_color=theme.accent_crimson, height=3, corner_radius=0)
        header.grid(row=0, column=0, sticky="ew")

        # Scrollable content
        content = ctk.CTkScrollableFrame(
            self, corner_radius=CORNER_RADIUS,
            fg_color=theme.bg_card, border_color=theme.border_default, border_width=1,
        )
        content.grid(row=1, column=0, sticky="nsew", padx=16, pady=(12, 8))
        content.grid_columnconfigure(0, weight=1)

        # ─── Section: URL ───────────────────────────────────────────────
        self._add_section_header(content, "URL", 0)
        self._url_entry = ctk.CTkEntry(
            content, placeholder_text="https://www.youtube.com/watch?v=...",
            corner_radius=CORNER_RADIUS, fg_color=theme.bg_input,
            border_color=theme.border_default, text_color=theme.text_primary,
            font=theme.font_body, border_width=1, height=40,
        )
        self._url_entry.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 16))

        # ─── Section: Format ─────────────────────────────────────────────
        self._add_section_header(content, "FORMAT", 2)
        self._format_var = ctk.StringVar(value=self._config.get("format", FORMAT_PRESETS[2][1]))
        self._format_menu = ctk.CTkOptionMenu(
            content, values=[p[0] for p in FORMAT_PRESETS],
            variable=self._format_var,
            command=self._on_format_change,
            corner_radius=CORNER_RADIUS, fg_color=theme.bg_input,
            button_color=theme.accent_brass, button_hover_color=theme.accent_crimson,
            text_color=theme.text_primary, font=theme.font_body,
            border_width=1, border_color=theme.border_default,
        )
        self._format_menu.grid(row=3, column=0, sticky="ew", padx=16, pady=(0, 4))

        # Custom format entry (hidden by default)
        self._custom_format_entry = ctk.CTkEntry(
            content, placeholder_text="Custom format string (e.g. bv[height<=720]+ba/best)",
            corner_radius=CORNER_RADIUS, fg_color=theme.bg_input,
            border_color=theme.border_default, text_color=theme.text_primary,
            font=theme.font_body, border_width=1, height=36,
        )
        self._custom_format_entry.grid(row=4, column=0, sticky="ew", padx=16, pady=(0, 16))
        self._custom_format_entry.grid_remove()

        # ─── Section: Subtitles ──────────────────────────────────────────
        self._add_section_header(content, "SUBTITLES", 5)
        self._write_subs_var = ctk.BooleanVar(value=self._config.get("write_subtitles", True))
        self._write_auto_var = ctk.BooleanVar(value=self._config.get("write_auto_subs", True))
        self._embed_subs_var = ctk.BooleanVar(value=self._config.get("embed_subtitles", True))

        chk_frame = ctk.CTkFrame(content, fg_color="transparent", corner_radius=0)
        chk_frame.grid(row=6, column=0, sticky="ew", padx=16, pady=(0, 4))

        for i, (text, var) in enumerate([
            ("Write subtitles", self._write_subs_var),
            ("Auto-generated", self._write_auto_var),
            ("Embed in video", self._embed_subs_var),
        ]):
            ctk.CTkCheckBox(
                chk_frame, text=text, variable=var,
                corner_radius=CORNER_RADIUS, border_width=2,
                fg_color=theme.accent_brass, hover_color=theme.accent_crimson,
                text_color=theme.text_primary, font=theme.font_body_sm,
            ).grid(row=0, column=i, padx=(0, 12))

        self._subs_lang_entry = ctk.CTkEntry(
            content, placeholder_text="zh-Hans,zh-Hant,en,ja",
            corner_radius=CORNER_RADIUS, fg_color=theme.bg_input,
            border_color=theme.border_default, text_color=theme.text_primary,
            font=theme.font_body, border_width=1, height=36,
        )
        self._subs_lang_entry.grid(row=7, column=0, sticky="ew", padx=16, pady=(0, 16))
        self._subs_lang_entry.insert(0, self._config.get("subtitle_langs", "zh-Hans,zh-Hant,en,ja"))

        # ─── Section: Proxy ──────────────────────────────────────────────
        self._add_section_header(content, "PROXY", 8)
        self._proxy_entry = ctk.CTkEntry(
            content, placeholder_text="socks5h://127.0.0.1:7897  (leave empty for direct)",
            corner_radius=CORNER_RADIUS, fg_color=theme.bg_input,
            border_color=theme.border_default, text_color=theme.text_primary,
            font=theme.font_body, border_width=1, height=36,
        )
        self._proxy_entry.grid(row=9, column=0, sticky="ew", padx=16, pady=(0, 16))
        if self._config.get("proxy"):
            self._proxy_entry.insert(0, self._config["proxy"])

        # ─── Section: Cookies ────────────────────────────────────────────
        self._add_section_header(content, "COOKIES", 10)
        cookies_frame = ctk.CTkFrame(content, fg_color="transparent", corner_radius=0)
        cookies_frame.grid(row=11, column=0, sticky="ew", padx=16, pady=(0, 16))
        cookies_frame.grid_columnconfigure(0, weight=1)

        self._cookies_entry = ctk.CTkEntry(
            cookies_frame, placeholder_text="Path to cookies.txt",
            corner_radius=CORNER_RADIUS, fg_color=theme.bg_input,
            border_color=theme.border_default, text_color=theme.text_primary,
            font=theme.font_body, border_width=1, height=36,
        )
        self._cookies_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        if self._config.get("cookies_path"):
            self._cookies_entry.insert(0, self._config["cookies_path"])

        from .widgets import EtchButton
        EtchButton(cookies_frame, text="BROWSE", width=80, height=36,
                   command=self._browse_cookies).grid(row=0, column=1)

        # ─── Section: Save Path ──────────────────────────────────────────
        self._add_section_header(content, "SAVE TO", 12)
        path_frame = ctk.CTkFrame(content, fg_color="transparent", corner_radius=0)
        path_frame.grid(row=13, column=0, sticky="ew", padx=16, pady=(0, 16))
        path_frame.grid_columnconfigure(0, weight=1)

        self._path_entry = ctk.CTkEntry(
            path_frame,
            corner_radius=CORNER_RADIUS, fg_color=theme.bg_input,
            border_color=theme.border_default, text_color=theme.text_primary,
            font=theme.font_body, border_width=1, height=36,
        )
        self._path_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self._path_entry.insert(0, self._config.get("save_path", os.path.expanduser("~/Downloads")))

        from .widgets import EtchButton
        EtchButton(path_frame, text="BROWSE", width=80, height=36,
                   command=self._browse_path).grid(row=0, column=1)

        # ─── Section: Player Client (Advanced) ──────────────────────────
        self._add_section_header(content, "PLAYER CLIENT", 14)
        self._player_var = ctk.StringVar(value="Default (web)")
        self._player_menu = ctk.CTkOptionMenu(
            content, values=[p[0] for p in PLAYER_CLIENT_OPTIONS],
            variable=self._player_var,
            corner_radius=CORNER_RADIUS, fg_color=theme.bg_input,
            button_color=theme.accent_brass, button_hover_color=theme.accent_crimson,
            text_color=theme.text_primary, font=theme.font_body,
            border_width=1, border_color=theme.border_default,
        )
        self._player_menu.grid(row=15, column=0, sticky="ew", padx=16, pady=(0, 16))

        # ─── Footer — Action buttons ────────────────────────────────────
        footer = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0, height=60)
        footer.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 16))
        footer.grid_columnconfigure(0, weight=1)

        from .widgets import BrassButton, DangerButton

        DangerButton(footer, text="CANCEL", width=120, height=40,
                     command=self._on_cancel).grid(row=0, column=0, sticky="w")

        BrassButton(footer, text="ADD TO QUEUE", width=160, height=40,
                    command=self._on_submit_click).grid(row=0, column=1, sticky="e")

    # ─── Helpers ────────────────────────────────────────────────────────────

    def _add_section_header(self, parent, text: str, row: int):
        """Add an uppercase label-caps section header with an etch underline."""
        label = ctk.CTkLabel(
            parent, text=text,
            font=theme.font_label, text_color=theme.text_secondary,
        )
        label.grid(row=row, column=0, sticky="w", padx=16, pady=(8, 2))

        # Etch underline — 1px crimson line
        line = ctk.CTkFrame(parent, height=1, fg_color=theme.accent_crimson, corner_radius=0)
        line.grid(row=row, column=0, sticky="ew", padx=16, pady=(0, 4))

    def _on_format_change(self, value: str):
        """Show/hide custom format entry based on preset selection."""
        preset_map = {p[0]: p[1] for p in FORMAT_PRESETS}
        if value == "Custom":
            self._custom_format_entry.grid()
            self._custom_format_entry.focus_set()
        else:
            self._custom_format_entry.grid_remove()

    def _browse_cookies(self):
        path = filedialog.askopenfilename(
            title="Select cookies file",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if path:
            self._cookies_entry.delete(0, "end")
            self._cookies_entry.insert(0, path)

    def _browse_path(self):
        path = filedialog.askdirectory(title="Select download folder")
        if path:
            self._path_entry.delete(0, "end")
            self._path_entry.insert(0, path)

    def _on_submit_click(self):
        """Gather all parameters and call the submit callback."""
        # Resolve format
        preset_map = {p[0]: p[1] for p in FORMAT_PRESETS}
        selected_format_label = self._format_var.get()
        if selected_format_label == "Custom":
            format_spec = self._custom_format_entry.get().strip()
            if not format_spec:
                format_spec = "bv[height<=1080]+ba/b[height<=1080]/best"
        else:
            format_spec = preset_map.get(selected_format_label, FORMAT_PRESETS[2][1])

        # Resolve player client
        player_client_map = {p[0]: p[1] for p in PLAYER_CLIENT_OPTIONS}
        player_client = player_client_map.get(self._player_var.get(), "web")

        self._result = {
            "url": self._url_entry.get().strip(),
            "save_path": self._path_entry.get().strip(),
            "format_spec": format_spec,
            "proxy": self._proxy_entry.get().strip(),
            "cookies_path": self._cookies_entry.get().strip(),
            "subtitle_langs": self._subs_lang_entry.get().strip(),
            "write_subtitles": self._write_subs_var.get(),
            "write_auto_subs": self._write_auto_var.get(),
            "embed_subtitles": self._embed_subs_var.get(),
            "merge_output_format": "mp4",
            "js_runtimes": "node",
            "player_client": player_client,
        }

        if self._on_submit:
            self._on_submit(self._result)
        self.destroy()

    def _on_cancel(self):
        self._result = None
        self.destroy()

    @property
    def result(self) -> dict | None:
        return self._result
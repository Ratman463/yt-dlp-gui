"""
Lucide icon loading for yt-dlp-gui.

Icons are pre-rendered transparent PNGs (generated from lucide SVGs)
stored in ``assets/icons``. This module wraps them in :class:`CTkImage`
so CustomTkinter scales them crisply for HiDPI displays.

The underlying PIL images are cached; the :class:`CTkImage` wrappers are
NOT — their internal PhotoImage handles bind to whichever Tk interpreter
was current at creation time, so sharing one wrapper across destroyed
and recreated Tk roots (as test suites do) breaks with ``TclError``.
Creating a wrapper per call is cheap (microseconds).
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import customtkinter as ctk
from PIL import Image

_ICONS_DIR = Path(__file__).resolve().parent / "assets" / "icons"

# Logical display size for inline (in-button) icons.
ICON_SIZE = (16, 16)


@lru_cache(maxsize=None)
def _pil(name: str) -> Image.Image:
    path = _ICONS_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"missing icon asset: {path}")
    return Image.open(path)


def _ctk(name: str, size: tuple[int, int]) -> ctk.CTkImage:
    img = _pil(name)
    return ctk.CTkImage(light_image=img, dark_image=img, size=size)


def browse_icon(size: tuple[int, int] = ICON_SIZE) -> ctk.CTkImage:
    """folder-open — used on the 浏览 path/cookies buttons."""
    return _ctk("folder-open-blue.png", size)


def chevron_down_slate(size: tuple[int, int] = ICON_SIZE) -> ctk.CTkImage:
    """chevron-down in slate — used on the format OptionMenu."""
    return _ctk("chevron-down-slate.png", size)


def chevron_down_blue(size: tuple[int, int] = ICON_SIZE) -> ctk.CTkImage:
    """chevron-down in accent blue — log toggle, collapsed state."""
    return _ctk("chevron-down-blue.png", size)


def chevron_up_blue(size: tuple[int, int] = ICON_SIZE) -> ctk.CTkImage:
    """chevron-up in accent blue — log toggle, expanded state."""
    return _ctk("chevron-up-blue.png", size)

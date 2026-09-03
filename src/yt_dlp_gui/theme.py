"""
SOFT_CARD design tokens for yt-dlp-gui.

A young, friendly "rounded card" aesthetic — pill buttons, pastel chips,
generous spacing, and a cool mist canvas. Surfaces are pure white cards
floating on the mist; actions are colorful filled pills.

Color palette
-------------
* Mist           (#eef0f7) — window canvas, cool light gray
* Card           (#ffffff) — cards / sheets / dialogs
* Ink            (#2b2d42) — primary text (deep indigo ink)
* Slate          (#7a7f9a) — secondary text
* Blue           (#3b82f6) — primary actions, focus, progress
* Rose           (#f4506c) — destructive actions, error states
* Mint           (#10b981) — success / finished states
* Amber          (#ff9f43) — warning / extracting states
* Sky chip       (#e3efff) — soft filled chips / secondary buttons

Shapes
------
Very soft geometry — 16px card corners, 20px large sheets, pill buttons
(radius auto-clamps to half the widget's height), and tube progress
tracks. Depth comes from surface contrast and hairline borders; no
shadows.
"""

from __future__ import annotations

import customtkinter as ctk

# ─── Colors ────────────────────────────────────────────────────────────────────

# Surfaces (Light Mode)
SURFACE = "#eef0f7"                  # Window canvas — lavender mist
SURFACE_CARD = "#ffffff"             # Cards / sheets / dialogs
SURFACE_SECONDARY = "#f1f2f8"        # Input wells / soft fills
SURFACE_TERTIARY = "#2b2d42"         # Used for inverted accents if needed

# Text
LABEL = "#2b2d42"                    # Primary text (deep indigo ink)
SECONDARY_LABEL = "#7a7f9a"          # Secondary text (slate)
TERTIARY_LABEL = "#a5aac4"           # Tertiary / disabled text
QUATERNARY_LABEL = "#c3c7d9"         # Placeholder / muted

# Separators & borders
SEPARATOR = "#e6e8f2"                # Hairline card border
SEPARATOR_OPAQUE = "#2b2d4214"       # ~8% ink

# ── Accent ramp ───────────────────────────────────────────────────────────────
# Primary — bright friendly blue. Young, calm, confident.
BLUE = "#3b82f6"
BLUE_HOVER = "#5c9cf8"
BLUE_PRESSED = "#2f6fe0"
BLUE_CONTAINER = "#e3efff"          # Soft sky fill for chips
BLUE_CONTAINER_HOVER = "#d6e7fd"
ON_BLUE = "#ffffff"
ON_BLUE_CONTAINER = "#1d5fd0"

# Destructive — soft rose (not alarm-red; friendlier for a young UI).
ROSE = "#f4506c"
ROSE_HOVER = "#ff647e"
ROSE_PRESSED = "#e03c57"
ROSE_CONTAINER = "#ffe7eb"
ROSE_CONTAINER_HOVER = "#ffd9e0"
ON_ROSE = "#ffffff"
ON_ROSE_CONTAINER = "#b32447"

# Status colors
MINT = "#10b981"                     # Success / finished
MINT_HOVER = "#2ecf94"
AMBER = "#ff9f43"                    # Warning / extracting
NEUTRAL = "#8b90a8"                  # Neutral accents

# Neutral chip (used for tertiary buttons like 取消)
CHIP_NEUTRAL = "#eceef5"
CHIP_NEUTRAL_HOVER = "#e1e4ee"

# Control backgrounds
CONTROL_BG = "#ffffff"               # Default controls
CONTROL_BG_DISABLED = "#f2f2f7"      # Disabled controls
CONTROL_BG_HOVER = SURFACE_SECONDARY # Hover state

# Fills
FILL_PRIMARY = "#2b2d42"             # Toggled / filled state
FILL_SECONDARY = "#eceef5"           # Secondary fills
FILL_TERTIARY = "#c3c7d9"            # Tertiary fills

# Legacy aliases kept for backward compat with tests/widgets
SURFACE_DIM = SURFACE_SECONDARY
SURFACE_BRIGHT = "#ffffff"
SURFACE_CONTAINER_LOWEST = "#ffffff"
SURFACE_CONTAINER_LOW = "#f7f8fc"
SURFACE_CONTAINER = SURFACE
SURFACE_CONTAINER_HIGH = "#e6e8f2"
SURFACE_CONTAINER_HIGHEST = "#dcdfe9"

ON_SURFACE = LABEL
ON_SURFACE_VARIANT = SECONDARY_LABEL
INVERSE_SURFACE = "#2b2d42"
INVERSE_ON_SURFACE = "#f4f5fa"

OUTLINE = "#c9cddd"
OUTLINE_VARIANT = "#e6e8f2"

PRIMARY = BLUE
ON_PRIMARY = ON_BLUE
PRIMARY_CONTAINER = BLUE_CONTAINER
ON_PRIMARY_CONTAINER = ON_BLUE_CONTAINER

SECONDARY = NEUTRAL
ON_SECONDARY = "#ffffff"
SECONDARY_CONTAINER = FILL_SECONDARY
ON_SECONDARY_CONTAINER = "#3a3d55"

ERROR = ROSE
ON_ERROR = ON_ROSE
ERROR_CONTAINER = ROSE_CONTAINER
ON_ERROR_CONTAINER = ON_ROSE_CONTAINER

# Legacy "system color" names — remapped onto the new palette.
SYSTEM_BLUE = BLUE                # Primary action / focus / progress
SYSTEM_BLUE_HOVER = BLUE_HOVER
SYSTEM_BLUE_PRESSED = BLUE_PRESSED
SYSTEM_RED = ROSE                   # Destructive / error
SYSTEM_RED_HOVER = ROSE_HOVER
SYSTEM_GREEN = MINT                 # Success
SYSTEM_ORANGE = AMBER               # Warning / pending
SYSTEM_GRAY = NEUTRAL               # Neutral accents

# Semantic tokens kept for compatibility with existing widgets
ETCH_COLOR = SEPARATOR              # Hairline separators
BRASS_HIGHLIGHT = BLUE            # Brass -> Blue
BRASS_ACTIVE = BLUE_PRESSED
CHARCOAL_BORDER = SEPARATOR
SUCCESS_GREEN = MINT


# ─── Typography ───────────────────────────────────────────────────────────────

# SF Pro on macOS, Segoe UI Variable / Segoe UI on Windows, Helvetica Neue
# fallback. CustomTkinter resolves these via Tk's font system.
FONT_DISPLAY = "SF Pro Display"
FONT_TEXT = "SF Pro Text"
FONT_MONO = "SF Mono"

# Cross-platform fallbacks — Tk will substitute these when SF Pro is missing.
FONT_DISPLAY_ALT = "Segoe UI"
FONT_TEXT_ALT = "Segoe UI"
FONT_MONO_ALT = "Consolas"


def _resolve_font(family: str, fallback: str, size: int, weight: str = "normal"):
    """Return a ``(family, size, weight)`` tuple resolved at runtime.

    The fallback is used only when :func:`refresh_fonts` runs against a
    Tk instance that reports the preferred family as missing. Until then
    we keep the preferred family so the tuple is stable for tests.
    """
    return (family, size, weight)


# Large Titles & Headlines — SF Pro Display (generously sized, friendly)
FONT_LARGE_TITLE = _resolve_font(FONT_DISPLAY, FONT_DISPLAY_ALT, 28, "bold")
FONT_TITLE_1 = _resolve_font(FONT_DISPLAY, FONT_DISPLAY_ALT, 22, "bold")
FONT_TITLE_2 = _resolve_font(FONT_DISPLAY, FONT_DISPLAY_ALT, 17, "bold")
FONT_TITLE_3 = _resolve_font(FONT_DISPLAY, FONT_DISPLAY_ALT, 15, "bold")

# Body — SF Pro Text
FONT_HEADLINE = _resolve_font(FONT_TEXT, FONT_TEXT_ALT, 15, "bold")
FONT_BODY = _resolve_font(FONT_TEXT, FONT_TEXT_ALT, 14, "normal")
FONT_BODY_LG = _resolve_font(FONT_TEXT, FONT_TEXT_ALT, 16, "normal")
FONT_BODY_SM = _resolve_font(FONT_TEXT, FONT_TEXT_ALT, 12, "normal")

# Captions
FONT_CAPTION = _resolve_font(FONT_TEXT, FONT_TEXT_ALT, 11, "normal")
FONT_CAPTION_BOLD = _resolve_font(FONT_TEXT, FONT_TEXT_ALT, 11, "bold")

# Backwards-compatible aliases used by existing widgets
FONT_H1 = FONT_TITLE_1
FONT_H2 = FONT_TITLE_2
FONT_H3 = FONT_TITLE_3
FONT_LABEL = FONT_CAPTION_BOLD
FONT_LABEL_SM = _resolve_font(FONT_TEXT, FONT_TEXT_ALT, 10, "bold")
FONT_NUMERAL = _resolve_font(FONT_TEXT, FONT_TEXT_ALT, 13, "bold")
FONT_NUMERAL_LG = _resolve_font(FONT_TEXT, FONT_TEXT_ALT, 17, "bold")

# ─── Spacing ──────────────────────────────────────────────────────────────────

# Breathing room is the point — the 4pt grid, used generously.
SPACING_UNIT = 4
SPACING_XS = 4
SPACING_SM = 8
SPACING_MD = 16
SPACING_LG = 24
SPACING_XL = 48
SPACING_GUTTER = 24
SPACING_MARGIN = 28

# ─── Shapes ────────────────────────────────────────────────────────────────────

# Soft rounded card geometry. CTk auto-clamps corner_radius to half the
# widget's smaller dimension, so CORNER_RADIUS_PILL renders as a perfect
# pill on any button / tube track.
CORNER_RADIUS = 16                  # Cards / inputs / dialogs
CORNER_RADIUS_SM = 12               # Small controls / menus
CORNER_RADIUS_LG = 20               # Large sheets
CORNER_RADIUS_PILL = 999            # Pill buttons / toggle tracks


# ─── Runtime font refresh ────────────────────────────────────────────────────


def refresh_fonts() -> None:
    """Re-resolve every font tuple against the families actually installed.

    Needs a (temporary) Tk root to enumerate font families. Falls back to
    the compiled preferred names on any failure. Safe to call multiple
    times — subsequent calls re-bind the module-level font tuples and the
    ones on :class:`ThemeColors`.
    """
    global FONT_LARGE_TITLE, FONT_TITLE_1, FONT_TITLE_2, FONT_TITLE_3
    global FONT_HEADLINE, FONT_BODY, FONT_BODY_LG, FONT_BODY_SM
    global FONT_CAPTION, FONT_CAPTION_BOLD, FONT_LABEL_SM
    global FONT_H1, FONT_H2, FONT_H3, FONT_LABEL, FONT_NUMERAL, FONT_NUMERAL_LG

    try:
        import tkinter as tk
        from tkinter import font as tkfont

        tmp_root = tk.Tk()
        tmp_root.withdraw()
        try:
            families = set(tkfont.families(tmp_root))
        finally:
            tmp_root.destroy()
    except Exception:
        return

    def pick(preferred: str, alt: str) -> str:
        return preferred if preferred in families else alt

    display = pick(FONT_DISPLAY, FONT_DISPLAY_ALT)
    text = pick(FONT_TEXT, FONT_TEXT_ALT)

    FONT_LARGE_TITLE = (display, 28, "bold")
    FONT_TITLE_1 = (display, 22, "bold")
    FONT_TITLE_2 = (display, 17, "bold")
    FONT_TITLE_3 = (display, 15, "bold")
    FONT_HEADLINE = (text, 15, "bold")
    FONT_BODY = (text, 14, "normal")
    FONT_BODY_LG = (text, 16, "normal")
    FONT_BODY_SM = (text, 12, "normal")
    FONT_CAPTION = (text, 11, "normal")
    FONT_CAPTION_BOLD = (text, 11, "bold")
    FONT_LABEL_SM = (text, 10, "bold")
    FONT_LABEL = FONT_CAPTION_BOLD
    FONT_H1 = FONT_TITLE_1
    FONT_H2 = FONT_TITLE_2
    FONT_H3 = FONT_TITLE_3
    FONT_NUMERAL = (text, 13, "bold")
    FONT_NUMERAL_LG = (text, 17, "bold")

    ThemeColors.font_large_title = FONT_LARGE_TITLE
    ThemeColors.font_title_1 = FONT_TITLE_1
    ThemeColors.font_title_2 = FONT_TITLE_2
    ThemeColors.font_title_3 = FONT_TITLE_3
    ThemeColors.font_headline = FONT_HEADLINE
    ThemeColors.font_h1 = FONT_H1
    ThemeColors.font_h2 = FONT_H2
    ThemeColors.font_h3 = FONT_H3
    ThemeColors.font_body = FONT_BODY
    ThemeColors.font_body_lg = FONT_BODY_LG
    ThemeColors.font_body_sm = FONT_BODY_SM
    ThemeColors.font_label = FONT_LABEL
    ThemeColors.font_label_sm = FONT_LABEL_SM
    ThemeColors.font_numeral = FONT_NUMERAL
    ThemeColors.font_numeral_lg = FONT_NUMERAL_LG


# ─── CustomTkinter theme ───────────────────────────────────────────────────────


def apply_theme() -> None:
    """Apply the SOFT_CARD design to CustomTkinter.

    Safe to call multiple times. Intended to run once at startup, before
    the main window is constructed.
    """
    # Light mode is the foundation — the mist canvas needs daylight.
    # (Widget/window scaling is left to CTk's automatic DPI detection so
    # the app stays crisp on HiDPI displays.)
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")
    refresh_fonts()


# ─── Centralized color/font access ────────────────────────────────────────────


class ThemeColors:
    """Centralized color and font access for all widgets.

    Attributes are class-level so they can be hot-swapped by
    :func:`refresh_fonts` after a Tk instance becomes available.
    """

    # Backgrounds
    bg_primary = SURFACE
    bg_card = SURFACE_CARD
    bg_input = SURFACE_SECONDARY
    bg_hover = SURFACE_SECONDARY
    bg_active = SURFACE_SECONDARY
    bg_secondary = SURFACE_SECONDARY

    # Text
    text_primary = LABEL
    text_secondary = SECONDARY_LABEL
    text_tertiary = TERTIARY_LABEL
    text_inverse = INVERSE_ON_SURFACE
    text_on_accent = ON_PRIMARY

    # Borders
    border_default = SEPARATOR
    border_strong = "#c9cddd"
    border_focus = BLUE

    # Accents
    accent_blue = BLUE
    accent_blue_hover = BLUE_HOVER
    accent_blue_pressed = BLUE_PRESSED
    accent_red = ROSE
    accent_red_hover = ROSE_HOVER
    accent_green = MINT
    accent_orange = AMBER
    accent_gray = NEUTRAL

    # Chips — soft filled secondary buttons
    chip_neutral = CHIP_NEUTRAL
    chip_neutral_hover = CHIP_NEUTRAL_HOVER
    primary_container = BLUE_CONTAINER
    primary_container_hover = BLUE_CONTAINER_HOVER
    on_primary_container = ON_BLUE_CONTAINER
    error_container = ROSE_CONTAINER
    error_container_hover = ROSE_CONTAINER_HOVER
    on_error_container = ON_ROSE_CONTAINER

    # Legacy aliases (kept for compatibility)
    accent_brass = BLUE
    accent_crimson = ROSE
    accent_success = MINT

    # Error
    error_bg = ERROR_CONTAINER
    error_text = ROSE

    # Fonts
    font_large_title = FONT_LARGE_TITLE
    font_title_1 = FONT_TITLE_1
    font_title_2 = FONT_TITLE_2
    font_title_3 = FONT_TITLE_3
    font_headline = FONT_HEADLINE
    font_h1 = FONT_H1
    font_h2 = FONT_H2
    font_h3 = FONT_H3
    font_body = FONT_BODY
    font_body_lg = FONT_BODY_LG
    font_body_sm = FONT_BODY_SM
    font_caption = FONT_CAPTION
    font_caption_bold = FONT_CAPTION_BOLD
    font_label = FONT_LABEL
    font_label_sm = FONT_LABEL_SM
    font_numeral = FONT_NUMERAL
    font_numeral_lg = FONT_NUMERAL_LG


theme = ThemeColors()

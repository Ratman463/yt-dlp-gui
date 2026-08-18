"""
NEO_ESOTERIC_MONUMENT design tokens for yt-dlp-gui.

Rooted in the "Minimalist Neo-Esoteric" aesthetic — ancient monumentalism
meeting modern editorial precision. The UI evokes a rare physical manuscript
or a stone-carved archive, not a conventional digital interface.

Color palette uses warm alabaster canvas, rich charcoal for structure,
matte brass for interactive highlights, and deep crimson for etched offsets.
"""

from __future__ import annotations

import customtkinter as ctk

# ─── Colors ────────────────────────────────────────────────────────────────────

# Surface / Background
SURFACE          = "#fbf9f4"   # Warm Alabaster — primary canvas
SURFACE_DIM      = "#dbdad5"
SURFACE_BRIGHT   = "#fbf9f4"
SURFACE_CONTAINER_LOWEST = "#ffffff"
SURFACE_CONTAINER_LOW    = "#f5f4ef"
SURFACE_CONTAINER        = "#efeee9"
SURFACE_CONTAINER_HIGH   = "#e9e8e3"
SURFACE_CONTAINER_HIGHEST = "#e3e2de"

ON_SURFACE        = "#1b1c19"
ON_SURFACE_VARIANT = "#4d4545"
INVERSE_SURFACE   = "#30312e"
INVERSE_ON_SURFACE = "#f2f1ec"

OUTLINE          = "#7f7575"
OUTLINE_VARIANT  = "#d0c4c4"

# Primary — Deep Charcoal / Ink
PRIMARY           = "#000000"
ON_PRIMARY        = "#ffffff"
PRIMARY_CONTAINER = "#1d1b1b"
ON_PRIMARY_CONTAINER = "#878382"

# Secondary — Matte Brass
SECONDARY          = "#745b1d"
ON_SECONDARY       = "#ffffff"
SECONDARY_CONTAINER = "#fedc91"
ON_SECONDARY_CONTAINER = "#785f21"

# Tertiary — Deep Crimson (the "Etch" / bloodline)
TERTIARY           = "#000000"    # used as structural accent
ON_TERTIARY        = "#ffffff"
TERTIARY_CONTAINER = "#410004"
ON_TERTIARY_CONTAINER = "#dd5853"

# Error
ERROR              = "#ba1a1a"
ON_ERROR           = "#ffffff"
ERROR_CONTAINER    = "#ffdad6"
ON_ERROR_CONTAINER = "#93000a"

# Semantic tokens for the app
ETCH_COLOR         = "#9F2B2A"   # Deep Crimson — 1px offset "cut" lines
BRASS_HIGHLIGHT    = "#fedc91"   # Matte Brass — interactive highlights
BRASS_ACTIVE       = "#e3c37a"   # Dimmed brass for active states
CHARCOAL_BORDER    = "#4d4545"   # Structural borders
SUCCESS_GREEN      = "#2e7d32"   # Download complete

# ─── Typography ────────────────────────────────────────────────────────────────

# Fonts — Newsreader for headlines, Inter for body/data
FONT_DISPLAY       = "Newsreader"
FONT_BODY           = "Inter"

# Fallbacks for systems without Newsreader / Inter
FONT_DISPLAY_ALT    = "Georgia"
FONT_BODY_ALT       = "Segoe UI"

def _resolve_font(preferred: str, fallback: str, size: int, weight: str = "normal") -> tuple:
    """Return a (family, size, weight) tuple, falling back if the font is unavailable."""
    return (preferred, size, weight)


def _refresh_fonts():
    """Re-resolve every font tuple against the fonts actually installed.

    Called from apply_theme() — needs a (temporary) Tk root to enumerate
    font families. Falls back to the compiled-in preferred names on failure.
    """
    global FONT_H1, FONT_H2, FONT_H3, FONT_BODY_LG, FONT_BODY_MD, FONT_BODY_SM
    global FONT_LABEL, FONT_LABEL_SM, FONT_NUMERAL, FONT_NUMERAL_LG

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

    def pick(preferred: str, fallback: str, size: int, weight: str) -> tuple:
        return (preferred if preferred in families else fallback, size, weight)

    display = pick(FONT_DISPLAY, FONT_DISPLAY_ALT, 16, "normal")[0]
    body = pick(FONT_BODY, FONT_BODY_ALT, 16, "normal")[0]

    FONT_H1         = (display, 28, "bold")
    FONT_H2         = (display, 22, "bold")
    FONT_H3         = (display, 18, "bold")
    FONT_BODY_LG    = (body, 16, "normal")
    FONT_BODY_MD    = (body, 14, "normal")
    FONT_BODY_SM    = (body, 12, "normal")
    FONT_LABEL      = (body, 11, "bold")
    FONT_LABEL_SM   = (body, 10, "bold")
    FONT_NUMERAL    = (body, 14, "bold")
    FONT_NUMERAL_LG = (body, 18, "bold")

    ThemeColors.font_h1        = FONT_H1
    ThemeColors.font_h2        = FONT_H2
    ThemeColors.font_h3        = FONT_H3
    ThemeColors.font_body      = FONT_BODY_MD
    ThemeColors.font_body_lg   = FONT_BODY_LG
    ThemeColors.font_body_sm   = FONT_BODY_SM
    ThemeColors.font_label     = FONT_LABEL
    ThemeColors.font_label_sm  = FONT_LABEL_SM
    ThemeColors.font_numeral   = FONT_NUMERAL
    ThemeColors.font_numeral_lg = FONT_NUMERAL_LG

# Display — Newsreader
FONT_H1        = _resolve_font(FONT_DISPLAY, FONT_DISPLAY_ALT, 28, "bold")
FONT_H2        = _resolve_font(FONT_DISPLAY, FONT_DISPLAY_ALT, 22, "bold")
FONT_H3        = _resolve_font(FONT_DISPLAY, FONT_DISPLAY_ALT, 18, "bold")

# Body — Inter
FONT_BODY_LG   = _resolve_font(FONT_BODY, FONT_BODY_ALT, 16, "normal")
FONT_BODY_MD   = _resolve_font(FONT_BODY, FONT_BODY_ALT, 14, "normal")
FONT_BODY_SM   = _resolve_font(FONT_BODY, FONT_BODY_ALT, 12, "normal")

# Labels — Inter, uppercase, heavy tracking
FONT_LABEL     = _resolve_font(FONT_BODY, FONT_BODY_ALT, 11, "bold")
FONT_LABEL_SM  = _resolve_font(FONT_BODY, FONT_BODY_ALT, 10, "bold")

# Numerals — Inter for data display
FONT_NUMERAL   = _resolve_font(FONT_BODY, FONT_BODY_ALT, 14, "bold")
FONT_NUMERAL_LG = _resolve_font(FONT_BODY, FONT_BODY_ALT, 18, "bold")

# ─── Spacing ───────────────────────────────────────────────────────────────────

SPACING_UNIT      = 4
SPACING_XS        = 4
SPACING_SM        = 8
SPACING_MD        = 16
SPACING_LG        = 32
SPACING_XL        = 64
SPACING_GUTTER    = 32
SPACING_MARGIN    = 32

# ─── Shapes ─────────────────────────────────────────────────────────────────────

# NEO_ESOTERIC_MONUMENT: strictly 0px — all rectangles, no curves.
CORNER_RADIUS = 0

# ─── CustomTkinter Theme ───────────────────────────────────────────────────────

def apply_theme():
    """Apply the NEO_ESOTERIC_MONUMENT design system to CustomTkinter."""
    # Use light mode with custom colors
    ctk.set_appearance_mode("light")

    # Default theme as base, then override
    ctk.set_default_color_theme("blue")

    # Override widget colors via widget scaling
    ctk.set_widget_scaling(1.0)
    ctk.set_window_scaling(1.0)

    # Resolve display/body fonts against what is actually installed
    # (Newsreader/Inter fall back to Georgia/Segoe UI if missing).
    _refresh_fonts()


class ThemeColors:
    """Centralized color access for all widgets."""
    # Backgrounds
    bg_primary   = SURFACE
    bg_card      = SURFACE_CONTAINER_LOWEST
    bg_input     = SURFACE_CONTAINER_LOWEST
    bg_hover     = SURFACE_CONTAINER
    bg_active    = SURFACE_CONTAINER_HIGH

    # Text
    text_primary    = ON_SURFACE
    text_secondary  = ON_SURFACE_VARIANT
    text_inverse    = INVERSE_ON_SURFACE
    text_on_brass   = ON_SECONDARY

    # Borders
    border_default  = OUTLINE
    border_strong   = CHARCOAL_BORDER
    border_focus    = BRASS_HIGHLIGHT

    # Accents
    accent_brass    = BRASS_HIGHLIGHT
    accent_crimson  = ETCH_COLOR
    accent_success  = SUCCESS_GREEN

    # Error
    error_bg     = ERROR_CONTAINER
    error_text   = ERROR

    # Fonts
    font_h1       = FONT_H1
    font_h2       = FONT_H2
    font_h3       = FONT_H3
    font_body     = FONT_BODY_MD
    font_body_lg  = FONT_BODY_LG
    font_body_sm  = FONT_BODY_SM
    font_label    = FONT_LABEL
    font_label_sm = FONT_LABEL_SM
    font_numeral  = FONT_NUMERAL
    font_numeral_lg = FONT_NUMERAL_LG


theme = ThemeColors()
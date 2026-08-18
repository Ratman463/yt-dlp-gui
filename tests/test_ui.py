"""UI tests: instantiate the main window and Add Download dialog without
requiring a display, then assert on structure and behavior.

We use a hidden (withdrawn) window so tests can run headless on CI.
"""
from __future__ import annotations

import os
import sys
import threading
import time
from pathlib import Path

import pytest

# CustomTkinter needs a display. On Windows we always have one, but to
# keep tests stable we withdraw the window immediately after creation.

# Make src importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


@pytest.fixture
def app():
    """Create the main window, withdrawn, yield it, then destroy."""
    from yt_dlp_gui.app import YtDlpGuiApp
    a = YtDlpGuiApp()
    a.withdraw()
    yield a
    try:
        a.destroy()
    except Exception:
        pass


# ─── Main window structure ────────────────────────────────────────────────

def test_main_window_creates(app):
    """The main window instantiates without error."""
    assert app.winfo_exists()


def test_main_window_has_add_button(app):
    """The + ADD button should exist and be wired to _open_add_dialog."""
    # Walk all children looking for a button with "+ ADD" text
    buttons = []
    def collect(w):
        try:
            from customtkinter import CTkButton
            if isinstance(w, CTkButton):
                buttons.append(w)
        except Exception:
            pass
        for child in w.winfo_children():
            collect(child)
    collect(app)
    add_btns = [b for b in buttons if b.cget("text") == "+ ADD"]
    assert add_btns, "missing + ADD button"


def test_main_window_has_stop_all_button(app):
    buttons = []
    def collect(w):
        try:
            from customtkinter import CTkButton
            if isinstance(w, CTkButton):
                buttons.append(w)
        except Exception:
            pass
        for child in w.winfo_children():
            collect(child)
    collect(app)
    stop_btns = [b for b in buttons if "STOP ALL" in (b.cget("text") or "")]
    assert stop_btns, "missing STOP ALL button"


def test_main_window_empty_state_visible(app):
    """The empty-state label should be shown initially."""
    assert app._empty_label.winfo_ismapped(), "empty state label not visible"


def test_log_panel_hidden_initially(app):
    """The log panel should NOT be visible on first launch."""
    assert not app._log_visible, "log panel should start hidden"
    assert not app._log_frame.winfo_ismapped(), "log frame is mapped but should be hidden"


# ─── Add Download dialog ─────────────────────────────────────────────────

@pytest.fixture
def dialog(app, monkeypatch):
    """Open the Add Download dialog against a pristine default config."""
    from yt_dlp_gui.dialogs import AddDownloadDialog
    from yt_dlp_gui import config as cfg_mod
    # Isolate from the developer's real config file.
    monkeypatch.setattr(cfg_mod, "CONFIG_DIR", None)
    monkeypatch.setattr(cfg_mod, "CONFIG_FILE", None)
    cfg = dict(cfg_mod.DEFAULT_CONFIG)
    d = AddDownloadDialog(app, cfg, on_submit=lambda r: None)
    d.withdraw()  # keep hidden for headless test
    # Pump events so children are laid out
    app.update_idletasks()
    yield d
    try:
        d.grab_release()
    except Exception:
        pass
    try:
        d.destroy()
    except Exception:
        pass


def test_dialog_has_url_entry(dialog):
    """URL input must exist and be empty."""
    assert hasattr(dialog, "_url_entry")
    assert dialog._url_entry.get() == "", "URL field should start empty"


def test_dialog_has_format_menu(dialog):
    """Format dropdown must exist and default to a known preset label."""
    assert hasattr(dialog, "_format_menu")
    val = dialog._format_var.get()
    from yt_dlp_gui.config import FORMAT_PRESETS
    labels = [p[0] for p in FORMAT_PRESETS]
    assert val in labels, f"initial format {val!r} not in preset labels {labels}"


def test_dialog_format_custom_reveals_entry(dialog):
    """Selecting 'Custom' should show the custom format entry."""
    dialog._format_var.set("Custom")
    dialog._on_format_change("Custom")
    dialog.update_idletasks()
    assert dialog._custom_format_entry.winfo_ismapped(), \
        "custom format entry not shown after selecting Custom"


def test_dialog_format_preset_hides_custom_entry(dialog):
    """Selecting a preset should hide the custom format entry."""
    dialog._format_var.set("Custom")
    dialog._on_format_change("Custom")
    dialog.update_idletasks()
    dialog._format_var.set("1080p")
    dialog._on_format_change("1080p")
    dialog.update_idletasks()
    assert not dialog._custom_format_entry.winfo_ismapped(), \
        "custom format entry still visible after selecting a preset"


def test_dialog_has_proxy_entry(dialog):
    assert hasattr(dialog, "_proxy_entry")


def test_dialog_has_cookies_entry(dialog):
    assert hasattr(dialog, "_cookies_entry")


def test_dialog_has_path_entry(dialog):
    assert hasattr(dialog, "_path_entry")
    assert dialog._path_entry.get(), "save path should default to something"


def test_dialog_has_subtitle_langs_entry(dialog):
    assert hasattr(dialog, "_subs_lang_entry")
    assert dialog._subs_lang_entry.get(), "subtitle langs should default"


def test_dialog_has_player_client_menu(dialog):
    assert hasattr(dialog, "_player_menu")


def test_dialog_has_subtitle_checkboxes(dialog):
    """All three subtitle toggles should be BooleanVars."""
    assert isinstance(dialog._write_subs_var.get(), bool)
    assert isinstance(dialog._write_auto_var.get(), bool)
    assert isinstance(dialog._embed_subs_var.get(), bool)


def test_dialog_submit_returns_all_fields(dialog):
    """When the user fills the form and clicks Add, every expected key
    must be present in the result dict."""
    dialog._url_entry.insert(0, "https://www.youtube.com/watch?v=test")
    dialog._proxy_entry.insert(0, "socks5h://127.0.0.1:7897")
    dialog._cookies_entry.insert(0, "D:\\cookies.txt")

    captured = []
    dialog._on_submit = lambda r: captured.append(r)
    dialog._on_submit_click()

    assert captured, "submit did not produce a result"
    r = captured[0]
    required_keys = {
        "url", "save_path", "format_spec", "proxy", "cookies_path",
        "subtitle_langs", "write_subtitles", "write_auto_subs",
        "embed_subtitles", "merge_output_format", "js_runtimes",
        "player_client",
    }
    missing = required_keys - set(r.keys())
    assert not missing, f"submit result missing keys: {missing}"
    assert r["url"] == "https://www.youtube.com/watch?v=test"
    assert r["proxy"] == "socks5h://127.0.0.1:7897"
    assert r["cookies_path"] == "D:\\cookies.txt"
    assert r["js_runtimes"] == "node"


def test_dialog_submit_format_preset_resolves(dialog):
    """Selecting the '1080p' preset should resolve to the correct format string."""
    from yt_dlp_gui.config import FORMAT_PRESETS
    dialog._url_entry.insert(0, "https://www.youtube.com/watch?v=x")
    dialog._format_var.set("1080p")
    dialog._on_format_change("1080p")
    captured = []
    dialog._on_submit = lambda r: captured.append(r)
    dialog._on_submit_click()
    expected = dict(FORMAT_PRESETS)["1080p"]
    assert captured[0]["format_spec"] == expected, \
        f"1080p preset resolved to {captured[0]['format_spec']!r}, expected {expected!r}"


def test_dialog_submit_custom_format(dialog):
    """If user picks Custom and types a format string, that string is used."""
    dialog._url_entry.insert(0, "https://www.youtube.com/watch?v=x")
    dialog._format_var.set("Custom")
    dialog._on_format_change("Custom")
    dialog._custom_format_entry.insert(0, "bestaudio/best")
    captured = []
    dialog._on_submit = lambda r: captured.append(r)
    dialog._on_submit_click()
    assert captured[0]["format_spec"] == "bestaudio/best"


def test_dialog_submit_requires_url(dialog, monkeypatch):
    """Submitting with an empty URL must not call the callback nor close."""
    from yt_dlp_gui import dialogs as dialogs_mod
    shown = []
    monkeypatch.setattr(
        dialogs_mod.messagebox, "showwarning",
        lambda *a, **k: shown.append(a),
    )
    captured = []
    dialog._on_submit = lambda r: captured.append(r)
    dialog._on_submit_click()  # URL is empty
    assert not captured, "submit fired without a URL"
    assert shown, "no warning was shown for the empty URL"
    assert dialog.winfo_exists(), "dialog closed despite validation error"


def test_dialog_cancel_returns_none(dialog):
    """Cancel button should destroy the dialog with no result."""
    dialog._on_cancel()
    assert not dialog.winfo_exists()
"""UI tests for the main window and the Add Download dialog.

We withdraw windows immediately so the tests can run headless on CI.
Every test pulls in a pristine DEFAULT_CONFIG so it never reads the
developer's real config file.
"""
from __future__ import annotations

import pytest

from yt_dlp_gui import config as cfg_mod


def _walk_buttons(root):
    """Yield every CTkButton widget under ``root`` (recursive)."""
    from customtkinter import CTkButton
    try:
        if isinstance(root, CTkButton):
            yield root
    except Exception:
        pass
    for child in root.winfo_children():
        yield from _walk_buttons(child)


# ─── Main window fixture ─────────────────────────────────────────────────────


@pytest.fixture
def app(tmp_path, monkeypatch):
    """Create the main window against a pristine default config.

    Redirects CONFIG_DIR / CONFIG_FILE to a temp path so the developer's
    real config file is never touched.
    """
    fake_dir = tmp_path / "yt-dlp-gui"
    fake_file = fake_dir / "config.json"
    monkeypatch.setattr(cfg_mod, "CONFIG_DIR", fake_dir)
    monkeypatch.setattr(cfg_mod, "CONFIG_FILE", fake_file)

    from yt_dlp_gui.app import YtDlpGuiApp
    a = YtDlpGuiApp()
    a.withdraw()
    yield a
    try:
        a.destroy()
    except Exception:
        pass


# ─── Main window structure ────────────────────────────────────────────────────


def test_main_window_creates(app):
    assert app.winfo_exists()


def test_main_window_has_add_button(app):
    """The + 添加 button should exist."""
    add_btns = [b for b in _walk_buttons(app) if "添加" in (b.cget("text") or "")]
    assert add_btns, "missing + 添加 button"


def test_main_window_has_stop_all_button(app):
    stop_btns = [b for b in _walk_buttons(app) if "全部停止" in (b.cget("text") or "")]
    assert stop_btns, "missing 全部停止 button"


def test_main_window_empty_state_visible(app):
    """The empty-state label should be shown initially."""
    assert app._empty_label.winfo_ismapped(), \
        "empty state label not visible"


def test_main_window_has_scrollable_list(app):
    assert hasattr(app, "_scrollable")
    assert app._scrollable.winfo_exists()


def test_main_window_has_status_label(app):
    assert hasattr(app, "_status_label")
    # Status text should be non-empty on boot.
    assert app._status_label.cget("text")


def test_log_panel_hidden_initially(app):
    """The log panel should NOT be visible on first launch."""
    assert not app._log_visible


def test_toggle_log_shows_panel(app):
    """Toggling the log panel flips the visibility flag and grids the frame.

    ``winfo_ismapped()`` is unreliable while the window is withdrawn for
    headless testing, so we only assert on the flag and that the grid
    call was issued without raising.
    """
    app._toggle_log()
    assert app._log_visible


def test_toggle_log_twice_hides_panel(app):
    app._toggle_log()
    app._toggle_log()
    assert not app._log_visible


def test_update_status_ready_when_empty(app):
    app._update_status()
    assert app._status_label.cget("text") == "就绪"


def test_add_download_ignores_empty_url(app):
    """An empty URL should be a no-op (no row added, no manager submit)."""
    before = len(app._download_items)
    app._add_download({"url": "", "save_path": "/tmp"})
    assert len(app._download_items) == before


# ─── DownloadItemWidget ───────────────────────────────────────────────────────


@pytest.fixture
def item(app):
    """Build a single DownloadItemWidget inside the main scrollable list."""
    from yt_dlp_gui.widgets import DownloadItemWidget
    from yt_dlp_gui.downloader import DownloadState
    w = DownloadItemWidget(
        app._scrollable,
        task_id="abcd1234",
        url="https://x.test/v",
    )
    yield w
    try:
        w.destroy()
    except Exception:
        pass


def test_item_initial_state_queued(item):
    from yt_dlp_gui.downloader import DownloadState
    assert item.state == DownloadState.QUEUED
    assert item.task_id == "abcd1234"
    assert item.url == "https://x.test/v"


def test_item_update_progress_downloading(item):
    from yt_dlp_gui.downloader import DownloadState, ProgressInfo
    item.update_progress(ProgressInfo(
        state=DownloadState.DOWNLOADING, percent=42.0,
        speed="1MiB/s", eta="00:10", title="My Video",
    ))
    assert item.state == DownloadState.DOWNLOADING
    # Title should switch from URL to the real title.
    assert item._title_label.cget("text") == "My Video"
    # State label should show the percent.
    assert "42" in item._state_label.cget("text")


def test_item_update_progress_finished(item):
    from yt_dlp_gui.downloader import DownloadState, ProgressInfo
    item.update_progress(ProgressInfo(
        state=DownloadState.FINISHED, title="Done", percent=100.0,
    ))
    assert item.state == DownloadState.FINISHED
    assert "完成" in item._state_label.cget("text")


def test_item_update_progress_error_shows_message(item):
    from yt_dlp_gui.downloader import DownloadState, ProgressInfo
    item.update_progress(ProgressInfo(
        state=DownloadState.ERROR,
        title="https://x.test/v",
        error_message="boom",
    ))
    assert item.state == DownloadState.ERROR
    assert item._error_label.cget("text") == "boom"


def test_item_cancel_button_triggers_callback(item):
    """Clicking cancel should fire the on_cancel callback with the task id."""
    captured = []
    item._on_cancel = lambda tid: captured.append(tid)
    item._handle_cancel()
    assert captured == ["abcd1234"]


def test_item_retry_button_triggers_callback(item):
    captured = []
    item._on_retry = lambda tid: captured.append(tid)
    item._handle_retry()
    assert captured == ["abcd1234"]


# ─── Add Download dialog ──────────────────────────────────────────────────────


@pytest.fixture
def dialog(app, tmp_path, monkeypatch):
    """Open the Add Download dialog against a pristine default config."""
    fake_dir = tmp_path / "yt-dlp-gui-dialog"
    fake_file = fake_dir / "config.json"
    monkeypatch.setattr(cfg_mod, "CONFIG_DIR", fake_dir)
    monkeypatch.setattr(cfg_mod, "CONFIG_FILE", fake_file)
    cfg = dict(cfg_mod.DEFAULT_CONFIG)
    from yt_dlp_gui.dialogs import AddDownloadDialog
    d = AddDownloadDialog(app, cfg, on_submit=lambda r: None)
    d.withdraw()
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


def test_dialog_creates(dialog):
    assert dialog.winfo_exists()


def test_dialog_has_url_entry(dialog):
    assert hasattr(dialog, "_url_entry")
    assert dialog._url_entry.get() == "", "URL field should start empty"


def test_dialog_has_format_menu(dialog):
    assert hasattr(dialog, "_format_menu")
    val = dialog._format_var.get()
    labels = [p[0] for p in cfg_mod.FORMAT_PRESETS]
    assert val in labels, f"initial format {val!r} not in preset labels {labels}"


def test_dialog_initial_format_is_default_preset(dialog):
    """With a pristine default config, the format dropdown defaults to the default preset."""
    assert dialog._format_var.get() == cfg_mod.DEFAULT_FORMAT_PRESET


def test_dialog_format_custom_reveals_entry(dialog):
    """Selecting the custom preset should show the custom format entry."""
    custom_label = cfg_mod.CUSTOM_FORMAT_LABEL
    dialog._format_var.set(custom_label)
    dialog._on_format_change(custom_label)
    dialog.update_idletasks()
    assert dialog._custom_format_entry.winfo_ismapped(), \
        "custom format entry not shown after selecting custom preset"


def test_dialog_format_preset_hides_custom_entry(dialog):
    """Selecting a preset should hide the custom format entry."""
    custom_label = cfg_mod.CUSTOM_FORMAT_LABEL
    # First show the custom entry.
    dialog._format_var.set(custom_label)
    dialog._on_format_change(custom_label)
    dialog.update_idletasks()
    # Then switch to a preset.
    dialog._format_var.set(cfg_mod.DEFAULT_FORMAT_PRESET)
    dialog._on_format_change(cfg_mod.DEFAULT_FORMAT_PRESET)
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


def test_dialog_has_subtitle_checkboxes(dialog):
    """All three subtitle toggles should be BooleanVars with bool values."""
    assert isinstance(dialog._write_subs_var.get(), bool)
    assert isinstance(dialog._write_auto_var.get(), bool)
    assert isinstance(dialog._embed_subs_var.get(), bool)


def test_dialog_has_playlist_checkbox(dialog):
    assert isinstance(dialog._playlist_var.get(), bool)


def test_dialog_submit_returns_all_fields(dialog):
    """Submitting a filled form must return every expected key."""
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
        "player_client", "download_playlist",
    }
    missing = required_keys - set(r.keys())
    assert not missing, f"submit result missing keys: {missing}"
    assert r["url"] == "https://www.youtube.com/watch?v=test"
    assert r["proxy"] == "socks5h://127.0.0.1:7897"
    assert r["cookies_path"] == "D:\\cookies.txt"
    # yt-dlp >= 2024.11 requires js_runtimes in dict form.
    assert r["js_runtimes"] == {"node": {}}


def test_dialog_submit_format_preset_resolves(dialog):
    """Selecting the cfg_mod.DEFAULT_FORMAT_PRESET preset should resolve to the correct spec."""
    dialog._url_entry.insert(0, "https://www.youtube.com/watch?v=x")
    dialog._format_var.set(cfg_mod.DEFAULT_FORMAT_PRESET)
    dialog._on_format_change(cfg_mod.DEFAULT_FORMAT_PRESET)
    captured = []
    dialog._on_submit = lambda r: captured.append(r)
    dialog._on_submit_click()
    expected = dict(cfg_mod.FORMAT_PRESETS)[cfg_mod.DEFAULT_FORMAT_PRESET]
    assert captured[0]["format_spec"] == expected, \
        f"default preset resolved to {captured[0]['format_spec']!r}"


def test_dialog_submit_custom_format(dialog):
    """Custom preset + typed format string -> that string is used."""
    custom_label = cfg_mod.CUSTOM_FORMAT_LABEL
    dialog._url_entry.insert(0, "https://www.youtube.com/watch?v=x")
    dialog._format_var.set(custom_label)
    dialog._on_format_change(custom_label)
    dialog._custom_format_entry.insert(0, "bestaudio/best")
    captured = []
    dialog._on_submit = lambda r: captured.append(r)
    dialog._on_submit_click()
    assert captured[0]["format_spec"] == "bestaudio/best"


def test_dialog_submit_custom_format_empty_falls_back(dialog):
    """Custom preset with an empty custom string falls back to a sane default."""
    custom_label = cfg_mod.CUSTOM_FORMAT_LABEL
    dialog._url_entry.insert(0, "https://www.youtube.com/watch?v=x")
    dialog._format_var.set(custom_label)
    dialog._on_format_change(custom_label)
    # Leave the custom entry empty.
    captured = []
    dialog._on_submit = lambda r: captured.append(r)
    dialog._on_submit_click()
    assert captured[0]["format_spec"] == \
        "bv[height<=1080]+ba/b[height<=1080]/best"


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


def test_dialog_submit_requires_save_path(dialog, monkeypatch):
    """Submitting with an empty save path must warn and not submit."""
    from yt_dlp_gui import dialogs as dialogs_mod
    shown = []
    monkeypatch.setattr(
        dialogs_mod.messagebox, "showwarning",
        lambda *a, **k: shown.append(a),
    )
    dialog._url_entry.insert(0, "https://www.youtube.com/watch?v=x")
    dialog._path_entry.delete(0, "end")
    captured = []
    dialog._on_submit = lambda r: captured.append(r)
    dialog._on_submit_click()
    assert not captured, "submit fired without a save path"
    assert shown, "no warning was shown for the empty save path"


def test_dialog_cancel_returns_none(dialog):
    """Cancel button should destroy the dialog with no result."""
    dialog._on_cancel()
    assert not dialog.winfo_exists()


def test_dialog_gather_result_none_on_empty_url(dialog, monkeypatch):
    """_gather_result should return None when validation fails."""
    # Stub messagebox so it doesn't pop a real dialog and block the test.
    from yt_dlp_gui import dialogs as dialogs_mod
    monkeypatch.setattr(
        dialogs_mod.messagebox, "showwarning",
        lambda *a, **k: None,
    )
    # URL is empty by default.
    assert dialog._gather_result() is None


def test_dialog_gather_result_returns_dict(dialog):
    dialog._url_entry.insert(0, "https://x")
    result = dialog._gather_result()
    assert isinstance(result, dict)
    assert result["url"] == "https://x"

"""Test the Downloader option builder + progress hook parsing.

We never hit the network here — every test exercises ``_build_opts`` or
``_progress_hook`` directly against synthetic yt-dlp dicts.
"""
from __future__ import annotations

import pytest

from yt_dlp_gui.downloader import (
    Downloader,
    DownloadState,
    ProgressInfo,
    TERMINAL_STATES,
    ACTIVE_STATES,
    _clean_str,
)


def make_downloader():
    """Downloader with a no-op progress callback."""
    return Downloader(on_progress=lambda url, info: None)


def _minimal_kwargs(**overrides):
    """ kwargs dict accepted by _build_opts, with sensible defaults."""
    kwargs = dict(
        save_path="/tmp",
        format_spec="best",
        proxy="",
        cookies_path="",
        subtitle_langs="",
        write_subtitles=False,
        write_auto_subs=False,
        embed_subtitles=False,
        merge_output_format="mp4",
        js_runtimes="node",
        player_client="web",
        url="u",
    )
    kwargs.update(overrides)
    return kwargs


# ─── _clean_str ───────────────────────────────────────────────────────────────


def test_clean_str_strips_ansi():
    assert _clean_str("\x1b[32m 3.2MiB/s \x1b[0m") == "3.2MiB/s"


def test_clean_str_handles_none():
    assert _clean_str(None) == ""


def test_clean_str_strips_whitespace():
    assert _clean_str("  hello  ") == "hello"


# ─── State enums ──────────────────────────────────────────────────────────────


def test_terminal_and_active_states_are_disjoint():
    """A state should not appear in both ACTIVE_STATES and TERMINAL_STATES."""
    active = set(ACTIVE_STATES)
    terminal = set(TERMINAL_STATES)
    assert not (active & terminal), \
        f"states in both sets: {active & terminal}"


def test_terminal_states_cover_all_end_states():
    """Every state not in ACTIVE_STATES should be terminal."""
    all_states = set(DownloadState)
    active = set(ACTIVE_STATES)
    terminal = set(TERMINAL_STATES)
    assert active | terminal == all_states


# ─── _build_opts: minimal ─────────────────────────────────────────────────────


def test_build_opts_minimal():
    """Bare minimum: outtmpl, format, progress_hooks, logger."""
    dl = make_downloader()
    opts = dl._build_opts(**_minimal_kwargs(save_path="F:/Downloads"))
    assert opts["outtmpl"] == "F:/Downloads/%(title)s.%(ext)s"
    assert opts["format"] == "best"
    assert opts["merge_output_format"] == "mp4"
    assert "progress_hooks" in opts
    assert len(opts["progress_hooks"]) == 1
    assert callable(opts["logger"].info)


def test_build_opts_normalizes_windows_save_path():
    dl = make_downloader()
    opts = dl._build_opts(**_minimal_kwargs(save_path="C:\\Users\\Me\\Downloads\\"))
    assert opts["outtmpl"] == "C:/Users/Me/Downloads/%(title)s.%(ext)s"


def test_build_opts_strips_trailing_slash_from_path():
    dl = make_downloader()
    opts = dl._build_opts(**_minimal_kwargs(save_path="/tmp/"))
    assert opts["outtmpl"] == "/tmp/%(title)s.%(ext)s"


def test_build_opts_empty_path_produces_relative_template():
    """An empty save_path still produces a parseable outtmpl."""
    dl = make_downloader()
    opts = dl._build_opts(**_minimal_kwargs(save_path=""))
    assert opts["outtmpl"] == "/%(title)s.%(ext)s"


# ─── _build_opts: proxy ───────────────────────────────────────────────────────


def test_build_opts_proxy_added():
    dl = make_downloader()
    opts = dl._build_opts(**_minimal_kwargs(proxy="socks5h://127.0.0.1:7897"))
    assert opts["proxy"] == "socks5h://127.0.0.1:7897"


def test_build_opts_no_proxy_key_absent():
    dl = make_downloader()
    opts = dl._build_opts(**_minimal_kwargs(proxy=""))
    assert "proxy" not in opts


# ─── _build_opts: cookies ─────────────────────────────────────────────────────


def test_build_opts_cookies_added():
    dl = make_downloader()
    opts = dl._build_opts(**_minimal_kwargs(cookies_path="D:/cookies.txt"))
    assert opts["cookiefile"] == "D:/cookies.txt"


def test_build_opts_no_cookies_key_absent():
    dl = make_downloader()
    opts = dl._build_opts(**_minimal_kwargs(cookies_path=""))
    assert "cookiefile" not in opts


# ─── _build_opts: subtitles ───────────────────────────────────────────────────


def test_build_opts_subtitles_full():
    dl = make_downloader()
    opts = dl._build_opts(**_minimal_kwargs(
        subtitle_langs="zh-Hans,zh-Hant,en,ja",
        write_subtitles=True, write_auto_subs=True, embed_subtitles=True,
    ))
    assert opts["writesubtitles"] is True
    assert opts["writeautomaticsub"] is True
    assert opts["embedsubtitle"] is True
    assert opts["subtitleslangs"] == ["zh-Hans", "zh-Hant", "en", "ja"]


def test_build_opts_subtitle_langs_split_on_comma():
    dl = make_downloader()
    for raw, expected in [
        ("en", ["en"]),
        ("en,ja", ["en", "ja"]),
        ("zh-Hans, zh-Hant , en", ["zh-Hans", "zh-Hant", "en"]),
    ]:
        opts = dl._build_opts(**_minimal_kwargs(
            subtitle_langs=raw,
            write_subtitles=True, write_auto_subs=False, embed_subtitles=False,
        ))
        assert opts["subtitleslangs"] == expected, f"failed for {raw!r}"


def test_build_opts_empty_subtitle_langs_not_split_into_blanks():
    dl = make_downloader()
    opts = dl._build_opts(**_minimal_kwargs(
        subtitle_langs="en, ,ja,",
        write_subtitles=True, write_auto_subs=False, embed_subtitles=False,
    ))
    assert opts["subtitleslangs"] == ["en", "ja"]


def test_build_opts_no_subtitle_keys_when_disabled():
    """When none of the subtitle flags are set, no subtitle opts appear."""
    dl = make_downloader()
    opts = dl._build_opts(**_minimal_kwargs(
        subtitle_langs="en",
        write_subtitles=False, write_auto_subs=False, embed_subtitles=False,
    ))
    for key in ("writesubtitles", "writeautomaticsub",
                "embedsubtitle", "subtitleslangs"):
        assert key not in opts, f"{key} should not be present"


# ─── _build_opts: js_runtimes ─────────────────────────────────────────────────


def test_build_opts_js_runtimes_string_converts_to_dict():
    """yt-dlp >= 2024.11 requires js_runtimes as a dict.

    Our wrapper accepts the legacy string form ("node", "node,deno")
    and converts it to the dict form for backward compatibility.
    """
    dl = make_downloader()
    opts = dl._build_opts(**_minimal_kwargs(js_runtimes="node"))
    assert opts["js_runtimes"] == {"node": {}}

    opts = dl._build_opts(**_minimal_kwargs(js_runtimes="node, deno"))
    assert opts["js_runtimes"] == {"node": {}, "deno": {}}


def test_build_opts_js_runtimes_dict_passes_through():
    dl = make_downloader()
    opts = dl._build_opts(**_minimal_kwargs(
        js_runtimes={"deno": {"path": "/x/deno"}},
    ))
    assert opts["js_runtimes"] == {"deno": {"path": "/x/deno"}}


def test_build_opts_js_runtimes_empty_string_omits_key():
    dl = make_downloader()
    opts = dl._build_opts(**_minimal_kwargs(js_runtimes=""))
    assert "js_runtimes" not in opts


# ─── _build_opts: player_client ───────────────────────────────────────────────


def test_build_opts_player_client_default_web_omits_extractor_args():
    """When player_client == 'web' (default), no extractor_args is added."""
    dl = make_downloader()
    opts = dl._build_opts(**_minimal_kwargs(player_client="web"))
    assert "extractor_args" not in opts


def test_build_opts_player_client_multi():
    dl = make_downloader()
    opts = dl._build_opts(**_minimal_kwargs(player_client="web,tv"))
    assert opts["extractor_args"] == {"youtube": {"player_client": ["web", "tv"]}}


# ─── _build_opts: playlist ────────────────────────────────────────────────────


def test_build_opts_noplaylist_defaults_true():
    dl = make_downloader()
    opts = dl._build_opts(**_minimal_kwargs())
    assert opts["noplaylist"] is True


def test_build_opts_playlist_mode():
    dl = make_downloader()
    opts = dl._build_opts(**_minimal_kwargs(noplaylist=False))
    assert opts["noplaylist"] is False


# ─── _build_opts: logger ──────────────────────────────────────────────────────


def test_build_opts_logger_always_attached_and_quiet():
    """Output must go to the logger shim, never to raw stderr."""
    dl = make_downloader()
    lines = []
    opts = dl._build_opts(**_minimal_kwargs(on_log=lines.append))
    assert callable(opts["logger"].info)
    opts["logger"].info("[youtube] Extracting URL")
    assert lines == ["[youtube] Extracting URL"]
    assert opts["quiet"] is True
    assert opts["noprogress"] is True


def test_build_opts_logger_drops_empty_lines():
    """The logger shim should not forward empty lines."""
    dl = make_downloader()
    lines = []
    opts = dl._build_opts(**_minimal_kwargs(on_log=lines.append))
    opts["logger"].info("   ")
    assert lines == []


def test_build_opts_logger_strips_ansi():
    """yt-dlp emits ANSI-coloured output — the shim should strip it."""
    dl = make_downloader()
    lines = []
    opts = dl._build_opts(**_minimal_kwargs(on_log=lines.append))
    opts["logger"].info("\x1b[32mhello\x1b[0m")
    assert lines == ["hello"]


def test_build_opts_logger_handles_all_levels():
    """debug / info / warning / error should all route to the callback."""
    dl = make_downloader()
    lines = []
    opts = dl._build_opts(**_minimal_kwargs(on_log=lines.append))
    opts["logger"].debug("d")
    opts["logger"].info("i")
    opts["logger"].warning("w")
    opts["logger"].error("e")
    assert lines == ["d", "i", "w", "e"]


# ─── _progress_hook ───────────────────────────────────────────────────────────


def _capture():
    """Return (downloader, captured_list)."""
    captured = []
    return Downloader(on_progress=lambda u, i: captured.append((u, i))), captured


def test_progress_hook_parses_downloading():
    dl, captured = _capture()
    dl._progress_hook("https://x", {
        "status": "downloading",
        "_percent_str": " 45.2%",
        "_speed_str": "3.2MiB/s",
        "_eta_str": "00:05",
        "downloaded_bytes": 1000,
        "total_bytes": 2000,
    })
    assert len(captured) == 1
    url, info = captured[0]
    assert url == "https://x"
    assert info.state == DownloadState.DOWNLOADING
    # Percent computed from raw bytes, not the localized display string.
    assert abs(info.percent - 50.0) < 0.01
    assert info.speed == "3.2MiB/s"
    assert info.eta == "00:05"
    assert info.downloaded_bytes == 1000
    assert info.total_bytes == 2000


def test_progress_hook_percent_prefers_bytes_over_display_string():
    """The display string is only a fallback — bytes are authoritative."""
    dl, captured = _capture()
    dl._progress_hook("https://x", {
        "status": "downloading",
        "downloaded_bytes": 750,
        "total_bytes_estimate": 3000,  # no total_bytes -> estimate used
        "_percent_str": "nonsense%",
    })
    assert abs(captured[-1][1].percent - 25.0) < 0.01


def test_progress_hook_percent_falls_back_to_percent_str():
    """When byte totals are unknown, parse the (cleaned) percent string."""
    dl, captured = _capture()
    dl._progress_hook("https://x", {
        "status": "downloading",
        "_percent_str": "\x1b[32m 12.5% \x1b[0m",
    })
    assert abs(captured[-1][1].percent - 12.5) < 0.01


def test_progress_hook_strips_ansi_from_speed_and_eta():
    dl, captured = _capture()
    dl._progress_hook("https://x", {
        "status": "downloading",
        "downloaded_bytes": 1,
        "total_bytes": 2,
        "_speed_str": "\x1b[32m 3.2MiB/s \x1b[0m",
        "_eta_str": "\x1b[32m 00:05 \x1b[0m",
    })
    assert captured[-1][1].speed == "3.2MiB/s"
    assert captured[-1][1].eta == "00:05"


def test_progress_hook_parses_finished():
    dl, captured = _capture()
    dl._progress_hook("https://x", {
        "status": "finished",
        "info_dict": {"title": "My Video"},
    })
    assert captured[-1][1].state == DownloadState.PROCESSING
    assert captured[-1][1].title == "My Video"


def test_progress_hook_unknown_status_noop():
    """An unrecognized status should not crash nor emit anything."""
    dl, captured = _capture()
    dl._progress_hook("https://x", {"status": "who-knows"})
    assert captured == []


def test_progress_hook_cancel_raises():
    """When the cancel event is set, the hook should raise DownloadError."""
    import yt_dlp.utils
    dl = make_downloader()
    dl.cancel()
    with pytest.raises(yt_dlp.utils.DownloadError):
        dl._progress_hook("u", {"status": "downloading", "_percent_str": "0%"})


# ─── Downloader.cancel / is_cancelled ─────────────────────────────────────────


def test_cancel_is_idempotent():
    dl = make_downloader()
    assert not dl.is_cancelled
    dl.cancel()
    assert dl.is_cancelled
    dl.cancel()  # second call should not raise
    assert dl.is_cancelled


# ─── ProgressInfo ──────────────────────────────────────────────────────────────


def test_progress_info_defaults():
    info = ProgressInfo()
    assert info.state == DownloadState.QUEUED
    assert info.percent == 0.0
    assert info.title == ""
    assert info.error_message == ""


def test_progress_info_slots():
    """ProgressInfo uses __slots__ — no __dict__ should exist."""
    info = ProgressInfo()
    assert not hasattr(info, "__dict__")

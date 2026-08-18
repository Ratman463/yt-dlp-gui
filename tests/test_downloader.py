"""Test the Downloader option builder without actually downloading."""
from __future__ import annotations

from unittest.mock import MagicMock

from yt_dlp_gui.downloader import Downloader, DownloadState, ProgressInfo


def make_downloader():
    """Downloader with a no-op callback."""
    return Downloader(on_progress=lambda url, info: None)


def test_build_opts_minimal():
    """Bare minimum: outtmpl, format, progress_hooks."""
    dl = make_downloader()
    opts = dl._build_opts(
        save_path="F:/Downloads",
        format_spec="bv+ba/best",
        proxy="",
        cookies_path="",
        subtitle_langs="",
        write_subtitles=False,
        write_auto_subs=False,
        embed_subtitles=False,
        merge_output_format="mp4",
        js_runtimes="node",
        player_client="web",
        url="https://example.com/v",
    )
    assert opts["outtmpl"] == "F:/Downloads/%(title)s.%(ext)s"
    assert opts["format"] == "bv+ba/best"
    assert opts["merge_output_format"] == "mp4"
    assert "progress_hooks" in opts
    assert len(opts["progress_hooks"]) == 1


def test_build_opts_proxy_added():
    dl = make_downloader()
    opts = dl._build_opts(
        save_path="/tmp", format_spec="best",
        proxy="socks5h://127.0.0.1:7897",
        cookies_path="", subtitle_langs="",
        write_subtitles=False, write_auto_subs=False, embed_subtitles=False,
        merge_output_format="mp4", js_runtimes="node",
        player_client="web", url="u",
    )
    assert opts["proxy"] == "socks5h://127.0.0.1:7897"


def test_build_opts_no_proxy_key_absent():
    dl = make_downloader()
    opts = dl._build_opts(
        save_path="/tmp", format_spec="best",
        proxy="",
        cookies_path="", subtitle_langs="",
        write_subtitles=False, write_auto_subs=False, embed_subtitles=False,
        merge_output_format="mp4", js_runtimes="node",
        player_client="web", url="u",
    )
    assert "proxy" not in opts


def test_build_opts_cookies_added():
    dl = make_downloader()
    opts = dl._build_opts(
        save_path="/tmp", format_spec="best",
        proxy="", cookies_path="D:/cookies.txt",
        subtitle_langs="",
        write_subtitles=False, write_auto_subs=False, embed_subtitles=False,
        merge_output_format="mp4", js_runtimes="node",
        player_client="web", url="u",
    )
    assert opts["cookiefile"] == "D:/cookies.txt"


def test_build_opts_subtitles():
    dl = make_downloader()
    opts = dl._build_opts(
        save_path="/tmp", format_spec="best",
        proxy="", cookies_path="",
        subtitle_langs="zh-Hans,zh-Hant,en,ja",
        write_subtitles=True, write_auto_subs=True, embed_subtitles=True,
        merge_output_format="mp4", js_runtimes="node",
        player_client="web", url="u",
    )
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
        opts = dl._build_opts(
            save_path="/tmp", format_spec="best",
            proxy="", cookies_path="", subtitle_langs=raw,
            write_subtitles=True, write_auto_subs=False, embed_subtitles=False,
            merge_output_format="mp4", js_runtimes="node",
            player_client="web", url="u",
        )
        assert opts["subtitleslangs"] == expected, f"failed for {raw!r}"


def test_build_opts_js_runtimes():
    dl = make_downloader()
    opts = dl._build_opts(
        save_path="/tmp", format_spec="best",
        proxy="", cookies_path="", subtitle_langs="",
        write_subtitles=False, write_auto_subs=False, embed_subtitles=False,
        merge_output_format="mp4", js_runtimes="node",
        player_client="web", url="u",
    )
    assert opts["js_runtimes"] == "node"


def test_build_opts_player_client_default_web_omits_extractor_args():
    """When player_client == 'web' (default), no extractor_args should be added."""
    dl = make_downloader()
    opts = dl._build_opts(
        save_path="/tmp", format_spec="best",
        proxy="", cookies_path="", subtitle_langs="",
        write_subtitles=False, write_auto_subs=False, embed_subtitles=False,
        merge_output_format="mp4", js_runtimes="node",
        player_client="web", url="u",
    )
    assert "extractor_args" not in opts


def test_build_opts_player_client_multi():
    dl = make_downloader()
    opts = dl._build_opts(
        save_path="/tmp", format_spec="best",
        proxy="", cookies_path="", subtitle_langs="",
        write_subtitles=False, write_auto_subs=False, embed_subtitles=False,
        merge_output_format="mp4", js_runtimes="node",
        player_client="web,tv", url="u",
    )
    assert opts["extractor_args"] == {"youtube": {"player_client": ["web", "tv"]}}


def test_progress_hook_parses_downloading():
    """Progress hook converts yt-dlp dict to ProgressInfo with correct state."""
    captured = []
    dl = Downloader(on_progress=lambda u, i: captured.append((u, i)))
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
    # Percent is computed from raw bytes, not the localized display string.
    assert abs(info.percent - 50.0) < 0.01
    assert info.speed == "3.2MiB/s"
    assert info.eta == "00:05"


def test_progress_hook_percent_prefers_bytes_over_display_string():
    """The display string is only a fallback — bytes are authoritative."""
    captured = []
    dl = Downloader(on_progress=lambda u, i: captured.append((u, i)))
    dl._progress_hook("https://x", {
        "status": "downloading",
        "downloaded_bytes": 750,
        "total_bytes_estimate": 3000,  # no total_bytes — estimate is used
        "_percent_str": "nonsense%",
    })
    assert abs(captured[-1][1].percent - 25.0) < 0.01


def test_progress_hook_percent_falls_back_to_percent_str():
    """When byte totals are unknown, parse the (cleaned) percent string."""
    captured = []
    dl = Downloader(on_progress=lambda u, i: captured.append((u, i)))
    dl._progress_hook("https://x", {
        "status": "downloading",
        "_percent_str": "\x1b[32m 12.5% \x1b[0m",
    })
    assert abs(captured[-1][1].percent - 12.5) < 0.01


def test_progress_hook_strips_ansi_from_speed_and_eta():
    captured = []
    dl = Downloader(on_progress=lambda u, i: captured.append((u, i)))
    dl._progress_hook("https://x", {
        "status": "downloading",
        "downloaded_bytes": 1,
        "total_bytes": 2,
        "_speed_str": "\x1b[32m 3.2MiB/s \x1b[0m",
        "_eta_str": "\x1b[32m 00:05 \x1b[0m",
    })
    assert captured[-1][1].speed == "3.2MiB/s"
    assert captured[-1][1].eta == "00:05"


def test_progress_hook_cancel_raises():
    """When cancel_event is set, the hook should raise DownloadError."""
    import yt_dlp.utils
    dl = make_downloader()
    dl.cancel()
    try:
        dl._progress_hook("u", {"status": "downloading", "_percent_str": "0%"})
        assert False, "should have raised"
    except yt_dlp.utils.DownloadError:
        pass


# ─── Option building: new behaviors ────────────────────────────────────────────

def _minimal_kwargs(**overrides):
    kwargs = dict(
        save_path="/tmp", format_spec="best",
        proxy="", cookies_path="", subtitle_langs="",
        write_subtitles=False, write_auto_subs=False, embed_subtitles=False,
        merge_output_format="mp4", js_runtimes="node",
        player_client="web", url="u",
    )
    kwargs.update(overrides)
    return kwargs


def test_build_opts_noplaylist_defaults_to_single_video():
    dl = make_downloader()
    opts = dl._build_opts(**_minimal_kwargs())
    assert opts["noplaylist"] is True


def test_build_opts_playlist_mode():
    dl = make_downloader()
    opts = dl._build_opts(**_minimal_kwargs(noplaylist=False))
    assert opts["noplaylist"] is False


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


def test_build_opts_normalizes_windows_save_path():
    dl = make_downloader()
    opts = dl._build_opts(**_minimal_kwargs(save_path="C:\\Users\\Me\\Downloads\\"))
    assert opts["outtmpl"] == "C:/Users/Me/Downloads/%(title)s.%(ext)s"


def test_build_opts_empty_subtitle_langs_not_split_into_blanks():
    dl = make_downloader()
    opts = dl._build_opts(**_minimal_kwargs(
        subtitle_langs="en, ,ja,",
        write_subtitles=True, write_auto_subs=False, embed_subtitles=False,
    ))
    assert opts["subtitleslangs"] == ["en", "ja"]


def test_progress_hook_parses_finished():
    captured = []
    dl = Downloader(on_progress=lambda u, i: captured.append((u, i)))
    dl._progress_hook("https://x", {
        "status": "finished",
        "info_dict": {"title": "My Video"},
    })
    assert captured[-1][1].state == DownloadState.PROCESSING
    assert captured[-1][1].title == "My Video"
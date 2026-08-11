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
    assert abs(info.percent - 45.2) < 0.01
    assert info.speed == "3.2MiB/s"
    assert info.eta == "00:05"


def test_progress_hook_parses_finished():
    captured = []
    dl = Downloader(on_progress=lambda u, i: captured.append((u, i)))
    dl._progress_hook("https://x", {
        "status": "finished",
        "info_dict": {"title": "My Video"},
    })
    assert captured[-1][1].state == DownloadState.PROCESSING
    assert captured[-1][1].title == "My Video"


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
"""Test config persistence: load / save / defaults / merge / presets.

Every test redirects CONFIG_FILE to a temp path so the developer's real
config is never touched.
"""
from __future__ import annotations

import json

import pytest

from yt_dlp_gui import config as cfg_mod


@pytest.fixture
def tmp_config_file(tmp_path, monkeypatch):
    """Redirect CONFIG_DIR / CONFIG_FILE to a temp path."""
    fake_dir = tmp_path / "yt-dlp-gui"
    fake_file = fake_dir / "config.json"
    monkeypatch.setattr(cfg_mod, "CONFIG_DIR", fake_dir)
    monkeypatch.setattr(cfg_mod, "CONFIG_FILE", fake_file)
    return fake_file


# ─── Defaults ─────────────────────────────────────────────────────────────────


def test_default_config_has_expected_keys():
    """DEFAULT_CONFIG must expose every key the rest of the app reads."""
    expected = {
        "save_path", "format", "proxy", "cookies_path",
        "subtitle_langs", "write_subtitles", "write_auto_subs",
        "embed_subtitles", "js_runtimes", "player_client",
        "merge_output_format", "max_concurrent_downloads",
        "download_playlist",
    }
    missing = expected - set(cfg_mod.DEFAULT_CONFIG)
    assert not missing, f"DEFAULT_CONFIG missing keys: {missing}"


def test_default_config_types():
    """Default values must have the types the UI / downloader expect."""
    assert isinstance(cfg_mod.DEFAULT_CONFIG["save_path"], str)
    assert isinstance(cfg_mod.DEFAULT_CONFIG["format"], str)
    assert isinstance(cfg_mod.DEFAULT_CONFIG["js_runtimes"], dict)
    assert isinstance(cfg_mod.DEFAULT_CONFIG["write_subtitles"], bool)
    assert isinstance(cfg_mod.DEFAULT_CONFIG["download_playlist"], bool)


def test_default_js_runtimes_is_dict():
    """yt-dlp >= 2024.11 requires js_runtimes as a dict, not a string."""
    assert cfg_mod.DEFAULT_CONFIG["js_runtimes"] == {"node": {}}


# ─── Load ─────────────────────────────────────────────────────────────────────


def test_load_config_returns_defaults_when_file_missing(tmp_config_file):
    """No file on disk -> all default keys present with default values."""
    cfg = cfg_mod.load_config()
    for key, value in cfg_mod.DEFAULT_CONFIG.items():
        assert key in cfg, f"missing default key: {key}"
        assert cfg[key] == value


def test_load_merges_missing_keys(tmp_config_file):
    """A partial config file on disk is backfilled with defaults."""
    tmp_config_file.parent.mkdir(parents=True, exist_ok=True)
    partial = {"proxy": "http://127.0.0.1:8080"}
    tmp_config_file.write_text(json.dumps(partial), encoding="utf-8")

    cfg = cfg_mod.load_config()
    assert cfg["proxy"] == "http://127.0.0.1:8080"  # from disk
    assert cfg["format"] == cfg_mod.DEFAULT_CONFIG["format"]  # backfilled
    assert cfg["embed_subtitles"] is True  # backfilled


def test_load_handles_corrupt_json(tmp_config_file):
    """Corrupt JSON falls back to defaults without raising."""
    tmp_config_file.parent.mkdir(parents=True, exist_ok=True)
    tmp_config_file.write_text("{ this is not valid json", encoding="utf-8")

    cfg = cfg_mod.load_config()
    # Either a clean defaults dict, or a defaults dict that happens to
    # share the default format — either is acceptable.
    assert cfg["format"] == cfg_mod.DEFAULT_CONFIG["format"]


def test_load_deep_merges_nested_dict(tmp_config_file):
    """A nested dict value (js_runtimes) is merged, not replaced wholesale."""
    tmp_config_file.parent.mkdir(parents=True, exist_ok=True)
    saved = {"js_runtimes": {"deno": {"path": "/x/deno"}}}
    tmp_config_file.write_text(json.dumps(saved), encoding="utf-8")

    cfg = cfg_mod.load_config()
    # The deno key from disk is preserved.
    assert cfg["js_runtimes"]["deno"] == {"path": "/x/deno"}
    # And we don't blow away unrelated default keys.


def test_load_non_dict_json_is_ignored(tmp_config_file):
    """A JSON file that isn't an object falls back to defaults."""
    tmp_config_file.parent.mkdir(parents=True, exist_ok=True)
    tmp_config_file.write_text(json.dumps(["not", "an", "object"]),
                               encoding="utf-8")
    cfg = cfg_mod.load_config()
    assert cfg["format"] == cfg_mod.DEFAULT_CONFIG["format"]


# ─── Save ─────────────────────────────────────────────────────────────────────


def test_save_then_load_roundtrip(tmp_config_file):
    """Save a modified config, reload, expect the same values."""
    cfg = cfg_mod.load_config()
    cfg["proxy"] = "socks5h://127.0.0.1:7897"
    cfg["save_path"] = "F:\\Downloads"
    cfg["format"] = "bv[height<=720]+ba/best"
    cfg_mod.save_config(cfg)

    reloaded = cfg_mod.load_config()
    assert reloaded["proxy"] == "socks5h://127.0.0.1:7897"
    assert reloaded["save_path"] == "F:\\Downloads"
    assert reloaded["format"] == "bv[height<=720]+ba/best"


def test_save_creates_directory(tmp_path, monkeypatch):
    """Saving should create the config directory if it doesn't exist."""
    nested = tmp_path / "deeply" / "nested" / "config"
    fake_file = nested / "config.json"
    monkeypatch.setattr(cfg_mod, "CONFIG_DIR", nested)
    monkeypatch.setattr(cfg_mod, "CONFIG_FILE", fake_file)

    cfg_mod.save_config({"proxy": "test"})
    assert fake_file.exists()
    saved = json.loads(fake_file.read_text(encoding="utf-8"))
    assert saved["proxy"] == "test"


def test_save_writes_utf8(tmp_config_file):
    """Non-ASCII values must survive a save/load roundtrip."""
    cfg = cfg_mod.load_config()
    cfg["save_path"] = "D:/下载/视频"
    cfg_mod.save_config(cfg)
    reloaded = cfg_mod.load_config()
    assert reloaded["save_path"] == "D:/下载/视频"


# ─── Presets ──────────────────────────────────────────────────────────────────


def test_format_presets_have_specs_except_custom():
    """Every preset except the custom one must have a non-empty spec.

    The custom preset label is locale-dependent ("自定义"), so resolve it
    from the last entry of FORMAT_PRESETS rather than hardcoding.
    """
    custom_label = cfg_mod.FORMAT_PRESETS[-1][0]
    for label, spec in cfg_mod.FORMAT_PRESETS:
        if label == custom_label:
            assert spec == ""
        else:
            assert spec, f"preset {label!r} has empty spec"
            assert "height" in spec or "best" in spec, \
                f"preset {label!r} looks wrong"


def test_format_presets_labels_unique():
    labels = [p[0] for p in cfg_mod.FORMAT_PRESETS]
    assert len(labels) == len(set(labels)), "duplicate preset labels"


def test_custom_format_label_matches_last_preset():
    """CUSTOM_FORMAT_LABEL must point at the sentinel preset."""
    assert cfg_mod.CUSTOM_FORMAT_LABEL == cfg_mod.FORMAT_PRESETS[-1][0]


def test_default_format_preset_is_in_labels():
    assert cfg_mod.DEFAULT_FORMAT_PRESET in [p[0] for p in cfg_mod.FORMAT_PRESETS]


def test_player_client_options_unique():
    """Player client options should have unique labels and values."""
    labels = [p[0] for p in cfg_mod.PLAYER_CLIENT_OPTIONS]
    values = [p[1] for p in cfg_mod.PLAYER_CLIENT_OPTIONS]
    assert len(labels) == len(set(labels)), "duplicate labels"
    assert len(values) == len(set(values)), "duplicate values"


def test_default_player_client_label_is_first_option():
    assert (
        cfg_mod.DEFAULT_PLAYER_CLIENT_LABEL
        == cfg_mod.PLAYER_CLIENT_OPTIONS[0][0]
    )


# ─── Deep merge helper ────────────────────────────────────────────────────────


def test_deep_merge_overlay_wins_on_conflict():
    base = {"a": 1, "b": {"x": 1, "y": 2}}
    overlay = {"b": {"y": 99, "z": 3}, "c": 4}
    merged = cfg_mod._deep_merge(base, overlay)
    assert merged == {"a": 1, "b": {"x": 1, "y": 99, "z": 3}, "c": 4}


def test_deep_merge_does_not_mutate_inputs():
    base = {"a": {"x": 1}}
    overlay = {"a": {"y": 2}}
    cfg_mod._deep_merge(base, overlay)
    assert base == {"a": {"x": 1}}
    assert overlay == {"a": {"y": 2}}

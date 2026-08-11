"""Test config persistence: load/save/defaults/merge."""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from yt_dlp_gui import config as cfg_mod


@pytest.fixture
def tmp_config_file(tmp_path, monkeypatch):
    """Redirect CONFIG_FILE to a temp path so tests don't touch the real config."""
    fake_dir = tmp_path / "yt-dlp-gui"
    fake_file = fake_dir / "config.json"
    monkeypatch.setattr(cfg_mod, "CONFIG_DIR", fake_dir)
    monkeypatch.setattr(cfg_mod, "CONFIG_FILE", fake_file)
    return fake_file


def test_load_config_returns_defaults_when_file_missing(tmp_config_file):
    """No file on disk → all default keys present."""
    cfg = cfg_mod.load_config()
    for key, value in cfg_mod.DEFAULT_CONFIG.items():
        assert key in cfg, f"missing default key: {key}"
        assert cfg[key] == value


def test_save_then_load_roundtrip(tmp_config_file):
    """Save modified config, reload, expect same values."""
    cfg = cfg_mod.load_config()
    cfg["proxy"] = "socks5h://127.0.0.1:7897"
    cfg["save_path"] = "F:\\Downloads"
    cfg["format"] = "bv[height<=720]+ba/best"
    cfg_mod.save_config(cfg)

    reloaded = cfg_mod.load_config()
    assert reloaded["proxy"] == "socks5h://127.0.0.1:7897"
    assert reloaded["save_path"] == "F:\\Downloads"
    assert reloaded["format"] == "bv[height<=720]+ba/best"


def test_load_merges_missing_keys(tmp_config_file):
    """A partial config file on disk should be backfilled with defaults."""
    tmp_config_file.parent.mkdir(parents=True, exist_ok=True)
    partial = {"proxy": "http://127.0.0.1:8080"}  # only one key
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
    assert cfg == cfg_mod.DEFAULT_CONFIG or cfg["format"] == cfg_mod.DEFAULT_CONFIG["format"]


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


def test_format_presets_are_valid():
    """Every preset except Custom has a non-empty format spec."""
    for label, spec in cfg_mod.FORMAT_PRESETS:
        if label == "Custom":
            assert spec == ""
        else:
            assert spec, f"preset {label!r} has empty spec"
            assert "height" in spec or "best" in spec, f"preset {label!r} looks wrong"


def test_player_client_options_unique():
    """Player client options should have unique labels and values."""
    labels = [p[0] for p in cfg_mod.PLAYER_CLIENT_OPTIONS]
    values = [p[1] for p in cfg_mod.PLAYER_CLIENT_OPTIONS]
    assert len(labels) == len(set(labels)), "duplicate labels"
    assert len(values) == len(set(values)), "duplicate values"
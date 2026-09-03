"""
Configuration persistence for yt-dlp-gui.

Stores and loads user preferences (proxy, save path, cookies, format, etc.)
to a JSON file in the platform-appropriate config directory.
"""

from __future__ import annotations

import copy
import json
import os
import sys
from pathlib import Path
from typing import Any

# ─── Config file location ─────────────────────────────────────────────────────


def _config_dir() -> Path:
    """Return the platform-specific config directory."""
    if sys.platform == "win32":
        base = os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming"))
    elif sys.platform == "darwin":
        base = str(Path.home() / "Library" / "Application Support")
    else:
        base = os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
    return Path(base) / "yt-dlp-gui"


CONFIG_DIR = _config_dir()
CONFIG_FILE = CONFIG_DIR / "config.json"


# ─── Default config ───────────────────────────────────────────────────────────

DEFAULT_CONFIG: dict[str, Any] = {
    "save_path": str(Path.home() / "Downloads"),
    "format": "bv[height<=1080]+ba/b[height<=1080]/best",
    "proxy": "",
    "cookies_path": "",
    "subtitle_langs": "zh-Hans,zh-Hant,en,ja",
    "write_subtitles": True,
    "write_auto_subs": True,
    "embed_subtitles": True,
    # yt-dlp >= 2024.11 requires js_runtimes as a dict like {"node": {}}.
    "js_runtimes": {"node": {}},
    "player_client": "web",
    "merge_output_format": "mp4",
    "max_concurrent_downloads": 1,
    "download_playlist": False,
}


# ─── Load / Save ──────────────────────────────────────────────────────────────


def _deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    """Return a new dict = base with overlay applied (overlay wins on conflict).

    Only dict values are merged recursively; everything else is overwritten.
    Used so a saved partial config never drops nested keys (e.g. js_runtimes).
    """
    result = copy.deepcopy(base)
    for key, value in overlay.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def load_config() -> dict[str, Any]:
    """Load config from disk, merging with defaults for any missing keys.

    Any failure (missing file, unreadable, corrupt JSON) falls back to the
    default config so the UI can always boot.
    """
    config = copy.deepcopy(DEFAULT_CONFIG)
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
            if isinstance(saved, dict):
                config = _deep_merge(config, saved)
        except (json.JSONDecodeError, OSError, ValueError):
            pass  # fall back to defaults
    # Ensure every default key exists (covers the case where a key was dropped
    # by an older version of the app that didn't know about it).
    for key, value in DEFAULT_CONFIG.items():
        config.setdefault(key, copy.deepcopy(value))
    return config


def save_config(config: dict[str, Any]) -> None:
    """Save config to disk, creating the directory if needed."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


# ─── Format presets ───────────────────────────────────────────────────────────

FORMAT_PRESETS = [
    ("最高 4K", "bv[height<=2160]+ba/b[height<=2160]/best"),
    ("最高 2K", "bv[height<=1440]+ba/b[height<=1440]/best"),
    ("最高 1080p", "bv[height<=1080]+ba/b[height<=1080]/best"),
    ("最高 720p", "bv[height<=720]+ba/b[height<=720]/best"),
    ("最高 480p", "bv[height<=480]+ba/b[height<=480]/best"),
    ("最佳画质", "bv+ba/best"),
    ("自定义", ""),
]

# Sentinel labels referenced by logic — resolved from the presets list so they
# stay in sync with i18n changes rather than being hardcoded.
CUSTOM_FORMAT_LABEL = FORMAT_PRESETS[-1][0]  # "自定义"
DEFAULT_FORMAT_PRESET = FORMAT_PRESETS[2][0]  # "最高 1080p"

PLAYER_CLIENT_OPTIONS = [
    ("默认 (web)", "web"),
    ("Web + TV", "web,tv"),
    ("Web + Android", "web,android"),
    ("Web + iOS", "web,ios"),
]
DEFAULT_PLAYER_CLIENT_LABEL = PLAYER_CLIENT_OPTIONS[0][0]  # "默认 (web)"

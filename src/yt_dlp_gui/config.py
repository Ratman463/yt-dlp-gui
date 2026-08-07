"""
Configuration persistence for yt-dlp-gui.

Stores and loads user preferences (proxy, save path, cookies, format, etc.)
to a JSON file in the platform-appropriate config directory.
"""

from __future__ import annotations

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
    "js_runtimes": "node",
    "player_client": "web",
    "merge_output_format": "mp4",
    "max_concurrent_downloads": 1,
}


# ─── Load / Save ──────────────────────────────────────────────────────────────

def load_config() -> dict[str, Any]:
    """Load config from disk, merging with defaults for any missing keys."""
    config = dict(DEFAULT_CONFIG)
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
            config.update(saved)
        except (json.JSONDecodeError, OSError):
            pass  # fall back to defaults
    # Ensure all default keys exist
    for key, value in DEFAULT_CONFIG.items():
        config.setdefault(key, value)
    return config


def save_config(config: dict[str, Any]) -> None:
    """Save config to disk, creating the directory if needed."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


# ─── Format presets ───────────────────────────────────────────────────────────

FORMAT_PRESETS = [
    ("2160p (4K)", "bv[height<=2160]+ba/b[height<=2160]/best"),
    ("1440p (2K)", "bv[height<=1440]+ba/b[height<=1440]/best"),
    ("1080p", "bv[height<=1080]+ba/b[height<=1080]/best"),
    ("720p", "bv[height<=720]+ba/b[height<=720]/best"),
    ("480p", "bv[height<=480]+ba/b[height<=480]/best"),
    ("Best", "bv+ba/best"),
    ("Custom", ""),
]

PLAYER_CLIENT_OPTIONS = [
    ("Default (web)", "web"),
    ("Web + TV", "web,tv"),
    ("Web + Android", "web,android"),
    ("Web + iOS", "web,ios"),
]
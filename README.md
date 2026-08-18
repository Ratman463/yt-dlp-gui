# yt-dlp-gui

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/CustomTkinter-5.2+-1A1C1E?style=flat-square" />
  <img src="https://img.shields.io/badge/license-MIT-410004?style=flat-square" />
</p>

A monumental video archive interface for [yt-dlp](https://github.com/yt-dlp/yt-dlp).

Built with Python + CustomTkinter, following the **Neo-Esoteric Monument** design system — warm alabaster canvas, charcoal borders, matte brass highlights, and deep crimson etch lines. Strictly rectangular. No shadows. No rounded corners.

## ✦ Features

- **Sequential download queue** — add multiple videos, they download one by one; the queue keeps accepting tasks after it drains
- **Per-task cancel & retry** — cancel a queued or active download without killing the rest of the queue; retry failed or cancelled tasks
- **Full parameter control** — format, subtitles, proxy, cookies, save path
- **Format presets** — 4K / 1080p / 720p / 480p / best, or custom format strings
- **Playlist handling** — download a single video or the entire playlist
- **Subtitle support** — write, auto-generate, embed subtitles with language selection
- **Proxy support** — HTTP / SOCKS5 proxy for region-locked content
- **Cookies import** — Netscape cookies.txt for authenticated content
- **JS runtime** — automatic Node.js detection for YouTube challenge solving
- **Config persistence** — remembers your proxy, path, format, and subtitle preferences
- **Log panel** — yt-dlp output routed into the GUI log viewer with per-task tags
- **Player client selection** — web, TV, Android, iOS client options

## ✦ Screenshots

> *Coming soon — the interface follows the Neo-Esoteric Monument design system with Warm Alabaster canvas, Matte Brass interactive elements, and Deep Crimson etch lines.*

## ✦ Installation

### From source

```bash
git clone https://github.com/Ratman463/yt-dlp-gui.git
cd yt-dlp-gui
pip install -e .
```

### Dependencies only

```bash
pip install -r requirements.txt
```

### Requirements

- Python 3.10+
- [Node.js](https://nodejs.org/) (recommended, for YouTube JS challenge solving)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) (installed automatically as dependency)

## ✦ Usage

```bash
python -m yt_dlp_gui
```

Or after `pip install -e .`:

```bash
yt-dlp-gui
```

## ✦ Design System

The UI follows the **Neo-Esoteric Monument** design system. See [DESIGN.md](DESIGN.md) for the full design token specification.

Key principles:

| Token | Value | Usage |
|:------|:------|:------|
| **Warm Alabaster** | `#fbf9f4` | Primary canvas background |
| **Rich Charcoal** | `#1b1c19` | Primary text and structural borders |
| **Matte Brass** | `#fedc91` | Interactive highlights, buttons, progress bars |
| **Deep Crimson** | `#9F2B2A` | Etch lines, error indicators, state accents |
| **Corner Radius** | `0px` | Strictly rectangular — no curves |
| **Newsreader** | Serif | Display headlines and editorial text |
| **Inter** | Sans-serif | Body text, labels, data |

The design evokes a rare physical manuscript — a stone-carved archive — rejecting standard digital conventions in favor of tactile minimalism and editorial precision.

## ✦ Project Structure

```
src/yt_dlp_gui/
├── __init__.py          # Package entry
├── __main__.py          # CLI entry: python -m yt_dlp_gui
├── app.py               # Main window — download list + log panel
├── config.py            # JSON config persistence + format presets
├── dialogs.py           # Add-download popup dialog
├── downloader.py        # yt-dlp Python API wrapper + queue manager
├── theme.py             # NEO_ESOTERIC_MONUMENT design tokens
└── widgets.py           # Custom widgets (BrassButton, EtchButton, etc.)
conftest.py              # Makes src/ importable for tests
tests/                   # 57 unit tests + network-gated integration tests
```

## ✦ Building

```bash
pip install pyinstaller
pyinstaller build.spec
```

The executable will be in `dist/yt-dlp-gui/`.

## ✦ License

MIT
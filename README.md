# yt-dlp-gui

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/CustomTkinter-5.2+-1A1C1E?style=flat-square" />
  <img src="https://img.shields.io/badge/license-MIT-410004?style=flat-square" />
</p>

A clean, friendly video download interface for [yt-dlp](https://github.com/yt-dlp/yt-dlp).

Built with Python + CustomTkinter in a **rounded card** style —
cool mist canvas, white pill-cornered cards, blue filled buttons,
and generous breathing room. Young, soft, and uncluttered.

## ✦ Features

- **Sequential download queue** — add multiple videos; they download one
  by one. The queue keeps accepting tasks even after it drains.
- **Per-task cancel & retry** — cancel a queued or active download
  without killing the rest of the queue; retry failed or cancelled tasks.
- **Full parameter control** — format, subtitles, proxy, cookies, save path.
- **Format presets** — 4K / 1440p / 1080p / 720p / 480p / best, or a
  custom format string.
- **Playlist handling** — download a single video or the entire playlist.
- **Subtitle support** — write, auto-generate, and embed subtitles with
  language selection.
- **Proxy support** — HTTP / SOCKS5 proxy for region-locked content.
- **Cookies import** — Netscape `cookies.txt` for authenticated content.
- **JS runtime** — automatic Node.js detection for YouTube challenge solving.
- **Config persistence** — remembers your proxy, path, format, and subtitle
  preferences between launches.
- **Log panel** — yt-dlp output routed into a collapsible GUI log viewer
  with per-task tags.

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
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) (installed automatically as a dependency)
- `yt_dlp_ejs` (installed automatically as a dependency — **required** for
  YouTube downloads since yt-dlp ≥ 2024.11; without it, YouTube fails with
  a misleading `The page needs to be reloaded` error)

## ✦ Usage

```bash
python -m yt_dlp_gui
```

Or after `pip install -e .`:

```bash
yt-dlp-gui
```

## ✦ Design System

The UI follows the **SOFT_CARD** rounded card style. See
[DESIGN.md](DESIGN.md) for the full design-token specification.

Key principles:

| Token              | Value     | Usage                                            |
| :----------------- | :-------- | :----------------------------------------------- |
| **Mist**           | `#eef0f7` | Window background — cool light-gray canvas      |
| **Card**           | `#ffffff` | Cards, inputs, and elevated surfaces             |
| **Ink**            | `#2b2d42` | Primary text — deep indigo ink                   |
| **Blue**         | `#3b82f6` | Primary actions, focus, progress bars            |
| **Rose**           | `#f4506c` | Destructive actions, error states                |
| **Mint**           | `#10b981` | Success / finished states                        |
| **Separator**      | `#e6e8f2` | Hairline card borders                            |
| **Corner Radius**  | `12–20px` | Cards 16px, inputs 12px, buttons pill-shaped     |
| **SF Pro Display** | Sans-serif| Titles and headlines                             |
| **SF Pro Text**    | Sans-serif| Body text, labels, controls                       |

The design is rooted in roundness and color — depth comes from surface
contrast (mist canvas vs. white cards) and hairline borders, never from
drop shadows. Every button is a pill; secondary actions are soft pastel
chips instead of bare text links.

## ✦ Project Structure

```
src/yt_dlp_gui/
├── __init__.py          # Package entry — exports main()
├── __main__.py          # CLI entry: python -m yt_dlp_gui
├── app.py               # Main window — download list + log panel
├── config.py            # JSON config persistence + format presets
├── dialogs.py           # Add-download popup dialog
├── downloader.py        # yt-dlp Python API wrapper + queue manager
├── theme.py             # SOFT_CARD design tokens
└── widgets.py           # Custom widgets (BrassButton, EtchButton, etc.)
conftest.py              # Makes src/ importable for tests
tests/                   # Unit tests (network-gated integration tests)
```

## ✦ Architecture

```
┌─────────────┐    submit(params)    ┌──────────────────────┐
│  app.py     │ ───────────────────► │  DownloadManager     │
│  (Tk main)  │ ◄─────────────────── │  (worker thread)     │
└─────────────┘   on_event(task_id,  └──────────┬───────────┘
                  url, ProgressInfo)            │ one per task
                                                ▼
                                       ┌──────────────────┐
                                       │  Downloader      │
                                       │  (yt-dlp wrapper)│
                                       └──────────────────┘
```

- `DownloadManager` owns a single persistent worker thread that drains an
  insertion-ordered FIFO. Cancelling one task never affects the others,
  and tasks submitted after the queue drains still run.
- Each task gets its own `Downloader` instance; `cancel()` on one
  instance cannot kill another.

## ✦ Testing

Unit tests (no network):

```bash
pytest
```

Including the network-gated integration tests (downloads a real sample):

```bash
pytest -m integration
```

## ✦ Building

```bash
pip install pyinstaller
pyinstaller build.spec
```

The executable will be in `dist/yt-dlp-gui/`.

## ✦ License

MIT

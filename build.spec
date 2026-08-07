# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for yt-dlp-gui."""

import sys
from pathlib import Path

block_cipher = None

# Project root
ROOT = Path(SPECPATH)

a = Analysis(
    [str(ROOT / "src" / "yt_dlp_gui" / "__main__.py")],
    pathex=[str(ROOT / "src")],
    binaries=[],
    datas=[],
    hiddenimports=[
        "yt_dlp",
        "customtkinter",
        "yt_dlp_gui",
        "yt_dlp_gui.theme",
        "yt_dlp_gui.config",
        "yt_dlp_gui.downloader",
        "yt_dlp_gui.widgets",
        "yt_dlp_gui.dialogs",
        "yt_dlp_gui.app",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="yt-dlp-gui",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
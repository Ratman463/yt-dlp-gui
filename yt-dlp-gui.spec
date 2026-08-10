# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['src/yt_dlp_gui/__main__.py'],
    pathex=[],
    binaries=[],
    datas=[('src', 'src')],
    hiddenimports=['yt_dlp', 'customtkinter', 'yt_dlp_gui', 'yt_dlp_gui.theme', 'yt_dlp_gui.config', 'yt_dlp_gui.downloader', 'yt_dlp_gui.widgets', 'yt_dlp_gui.dialogs', 'yt_dlp_gui.app'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='yt-dlp-gui',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='yt-dlp-gui',
)

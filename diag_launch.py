"""Diagnostic launch: runs the real GUI with stderr diagnostics."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from yt_dlp_gui.theme import apply_theme
from yt_dlp_gui.app import YtDlpGuiApp

if __name__ == "__main__":
    print("=== yt-dlp-gui diagnostic launch ===", file=sys.stderr)
    print(f"Python: {sys.version}", file=sys.stderr)
    import customtkinter as ctk
    print(f"CustomTkinter: {ctk.__version__}", file=sys.stderr)

    apply_theme()
    app = YtDlpGuiApp()
    print("Main window created OK", file=sys.stderr)
    print("Now click '+ 添加', type a URL, click '添加到队列'", file=sys.stderr)
    print("Watch this console for [diag] lines", file=sys.stderr)
    app.mainloop()

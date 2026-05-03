"""Entry point for PyInstaller — bootstraps claude_backend as a package.

Modes:
  ClaudeTokenSaver.exe          → opens GUI window (default)
  ClaudeTokenSaver.exe --tray   → starts system-tray icon only
"""

import sys
from pathlib import Path

# When frozen by PyInstaller, _MEIPASS points to the temp extraction dir.
# claude_backend is bundled as data there, so add it to sys.path.
if getattr(sys, "frozen", False):
    base = Path(sys._MEIPASS)
    sys.path.insert(0, str(base))
else:
    sys.path.insert(0, str(Path(__file__).resolve().parent))


def _is_tray_mode() -> bool:
    """Tray mode if --tray (or -t) anywhere in argv. Other args ignored."""
    return any(a in ("--tray", "-t") for a in sys.argv[1:])


if __name__ == "__main__":
    if _is_tray_mode():
        from claude_backend.tray import run as tray_run
        sys.exit(tray_run())
    from claude_backend.gui import main
    main()

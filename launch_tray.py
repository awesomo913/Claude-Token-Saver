"""Entry point for tray-only mode — runs the system tray icon.

Use this for Windows autostart shortcuts. Launches the persistent
tray icon without opening the GUI window. User clicks the tray icon
to open the GUI on demand.
"""

import sys
from pathlib import Path

if getattr(sys, "frozen", False):
    base = Path(sys._MEIPASS)
    sys.path.insert(0, str(base))
else:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from claude_backend.tray import run

if __name__ == "__main__":
    sys.exit(run())

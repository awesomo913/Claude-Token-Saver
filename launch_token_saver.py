"""Entry point for PyInstaller — bootstraps claude_backend as a package."""

import sys
import os
from pathlib import Path

# When frozen by PyInstaller, _MEIPASS points to the temp extraction dir.
# claude_backend is bundled as data there, so add it to sys.path.
if getattr(sys, 'frozen', False):
    base = Path(sys._MEIPASS)
    sys.path.insert(0, str(base))
else:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from claude_backend.gui import main

if __name__ == "__main__":
    main()

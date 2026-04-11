"""Click-to-launch Gemini Coder Web Edition (no console window)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gemini_coder_web.__main__ import main

if __name__ == "__main__":
    main()

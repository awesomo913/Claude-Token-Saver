"""Entry point for Gemini Coder Web Edition."""

import io
import logging
import sys

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from . import __version__, __app_name__


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    from .ui.app_web import GeminiCoderWebApp
    app = GeminiCoderWebApp()
    app.mainloop()


if __name__ == "__main__":
    main()

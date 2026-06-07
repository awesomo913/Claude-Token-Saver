"""Standalone HTTP server boot — belt-and-suspenders fallback for SessionStart.

Starts ONLY the Token Saver HTTP backend (port 7321).  No tray icon, no GUI.
Intended to be spawned as an async hook so the overlay picker always has a
server to talk to even if the exe tray launch failed.

Usage (hook command):
    pythonw -m claude_backend.http_server_boot

Behaviour:
  - If port 7321 is already responding → exit 0 silently (idempotent).
  - If not → start the HTTP server thread and block until process is killed.
  - All errors logged; never raises to the caller.
"""

from __future__ import annotations

import datetime
import logging
import signal
import sys
import time
import urllib.request
from pathlib import Path

logging.basicConfig(
    level=logging.WARNING,
    format="%(levelname)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)

_HTTP_PORT = 7321


def _log(msg: str) -> None:
    try:
        log_dir = (
            Path.home()
            / ".claude"
            / "session-data"
            / datetime.date.today().isoformat()
        )
        log_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.datetime.now().isoformat(timespec="seconds")
        with open(log_dir / "exe_ClaudeTokenSaver.log", "a", encoding="utf-8") as fh:
            fh.write(f"{ts} {msg}\n")
    except OSError as exc:
        logger.debug("http_server_boot: log write failed: %s", exc)


def _already_running(port: int = _HTTP_PORT, timeout: float = 1.0) -> bool:
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=timeout)
        return True
    except Exception:
        return False


def main() -> int:
    if _already_running():
        _log("http_server_boot: server already up, exit 0")
        return 0

    try:
        from claude_backend.http_server import start_server
        from claude_backend.prefs import Prefs
        prefs = Prefs.load()
        port = getattr(prefs, "http_port", _HTTP_PORT)
    except Exception as exc:
        _log(f"http_server_boot: import failed: {exc}")
        logger.warning("http_server_boot: import failed: %s", exc)
        return 1

    if start_server(port):
        _log(f"http_server_boot: started on 127.0.0.1:{port}")
    else:
        _log(f"http_server_boot: start_server({port}) returned False (port in use?)")
        return 0  # another process may have just claimed it — not a hard error

    # Keep process alive so the daemon thread doesn't die.
    # Responds to SIGTERM / KeyboardInterrupt cleanly.
    def _shutdown(*_args: object) -> None:
        _log("http_server_boot: shutdown signal received")
        sys.exit(0)

    signal.signal(signal.SIGTERM, _shutdown)
    try:
        while True:
            time.sleep(30)
    except KeyboardInterrupt:
        _log("http_server_boot: KeyboardInterrupt, exiting")

    return 0


if __name__ == "__main__":
    sys.exit(main())

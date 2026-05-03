"""Session launcher — invoked by Claude Code SessionStart hook.

Purpose: optionally auto-open Token Saver (full GUI window or tray)
when a Claude Code session starts. Behavior is gated by user prefs:

- prefs.auto_launch_gui_on_session == False (default) → exit silently
- prefs.auto_launch_gui_on_session == True → spawn the exe
  - prefs.auto_launch_minimized == True (default) → exe --tray
  - prefs.auto_launch_minimized == False → exe (full GUI window)

Single-instance enforced: if a tray (or another launcher) is already
running, this exits without spawning a duplicate.

Run via:
  python -m claude_backend.session_launcher

The hook command in ~/.claude/settings.json invokes this module.
The script exits 0 in all normal cases (success, opt-out, already
running) so it never blocks Claude Code session startup.
"""

from __future__ import annotations

import logging
import os
import subprocess
import sys
from pathlib import Path

from .prefs import Prefs
from .single_instance import is_locked

logger = logging.getLogger(__name__)

# Same name used by tray.run() — both compete for the same lock.
_TRAY_INSTANCE_NAME = "ClaudeTokenSaverTray"

# Where the deployed exe is expected to live. Used as primary launch target
# when running from a frozen/installed environment. Falls back to running
# the gui module from source if the exe path doesn't exist.
_DEFAULT_EXE_PATH = Path.home() / "Desktop" / "ClaudeTokenSaver" / "ClaudeTokenSaver.exe"


def _find_exe() -> Path | None:
    """Locate ClaudeTokenSaver.exe on disk. Prefer Desktop deploy."""
    if _DEFAULT_EXE_PATH.is_file():
        return _DEFAULT_EXE_PATH
    # Could extend with PATH lookup or registry in future; for now, just Desktop.
    return None


def _spawn_detached(args: list[str]) -> bool:
    """Spawn a detached subprocess so the hook can return immediately.

    Returns True on success. Errors are logged, never raised — we must
    not block Claude Code session start.
    """
    try:
        kwargs: dict = {"close_fds": True}
        if sys.platform == "win32":
            kwargs["creationflags"] = (
                subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS
            )
        else:
            # POSIX: detach via setsid so spawned process survives parent exit.
            kwargs["start_new_session"] = True
        subprocess.Popen(args, **kwargs)
        return True
    except OSError as e:
        logger.warning("session_launcher: spawn failed: %s", e)
        return False


def main() -> int:
    """Entry point. Always exits 0 to avoid blocking session start."""
    # Lazy logging — only set up if something interesting happens.
    prefs = Prefs.load()

    if not prefs.auto_launch_gui_on_session:
        return 0

    # Don't double-launch if tray (or another launcher) is already running.
    # is_locked() does a non-acquiring check via PID lockfile.
    if is_locked(_TRAY_INSTANCE_NAME):
        return 0

    exe = _find_exe()
    if exe is None:
        # Frozen exe missing — try running the GUI from source via Python.
        # This is the fallback for users running from a dev checkout.
        python_args: list[str] = []
        # Prefer pythonw on Windows to avoid console flash.
        py = sys.executable
        if sys.platform == "win32":
            cand = Path(py).with_name("pythonw.exe")
            if cand.is_file():
                py = str(cand)
        python_args = [py, "-m", "claude_backend.gui"]
        if prefs.auto_launch_minimized:
            # Source path for tray-only mode goes through the launcher script.
            python_args = [py, "-m", "claude_backend", "tray"]
        _spawn_detached(python_args)
        return 0

    args: list[str] = [str(exe)]
    if prefs.auto_launch_minimized:
        args.append("--tray")
    _spawn_detached(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())

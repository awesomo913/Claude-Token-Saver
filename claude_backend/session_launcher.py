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

import datetime
import logging
import os
import subprocess
import sys
import threading
import urllib.request
from pathlib import Path

from .prefs import Prefs
from .single_instance import _pidfile_path  # internal helper, OK locally
from .single_instance import is_locked

logger = logging.getLogger(__name__)

# Lock names — must match what tray.run() and gui.main() acquire.
_TRAY_INSTANCE_NAME = "ClaudeTokenSaverTray"
_GUI_INSTANCE_NAME = "ClaudeTokenSaverGUI"

_HTTP_PORT = 7321


def _log_session(msg: str) -> None:
    """Append one timestamped line to today's session log. Never raises."""
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
        logger.debug("session_launcher: log write failed: %s", exc)


def _http_is_alive(port: int = _HTTP_PORT, timeout: float = 1.0) -> bool:
    """Return True if the Token Saver HTTP server responds on localhost."""
    try:
        urllib.request.urlopen(
            f"http://127.0.0.1:{port}/projects", timeout=timeout
        )
        return True
    except Exception:
        return False


def _clear_stale_lock(name: str) -> bool:
    """Remove pidfile if the recorded PID is dead or reused by another process.

    Returns True if a stale entry was cleared, False if lock is genuinely held
    or no pidfile exists.
    """
    pidfile = _pidfile_path(name)
    if not pidfile.is_file():
        return False
    try:
        existing_pid = int(pidfile.read_text(encoding="utf-8").strip())
    except (ValueError, OSError):
        return False
    if existing_pid <= 0:
        return False
    try:
        import psutil
        if not psutil.pid_exists(existing_pid):
            pidfile.unlink(missing_ok=True)
            return True
        # PID exists but may be a different process that reused the slot.
        # Use HTTP liveness as a secondary signal: if the tray were running
        # its server would respond.
        if not _http_is_alive():
            pidfile.unlink(missing_ok=True)
            return True
    except ImportError:
        # No psutil — skip dead-PID check, rely on HTTP signal only.
        if not _http_is_alive():
            try:
                pidfile.unlink(missing_ok=True)
                return True
            except OSError as exc:
                logger.warning("session_launcher: could not remove stale pidfile: %s", exc)
    except OSError as exc:
        logger.warning("session_launcher: stale-lock check failed: %s", exc)
    return False


def _verify_http_in_background(timeout_s: float = 10.0) -> None:
    """Poll HTTP server in a background thread and log when it comes up (or times out)."""
    def _poll() -> None:
        import time
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            if _http_is_alive():
                _log_session("session_launcher: http=up (verified after spawn)")
                return
            time.sleep(1.5)
        _log_session("session_launcher: http=down after spawn (server did not respond within 10s)")
    threading.Thread(target=_poll, daemon=True, name="ts_http_verify").start()

# Where the deployed exe is expected to live. Used as primary launch target
# when running from a frozen/installed environment. Falls back to running
# the gui module from source if the exe path doesn't exist.
_DEFAULT_EXE_PATH = Path.home() / "Desktop" / "My Apps" / "ClaudeTokenSaver" / "ClaudeTokenSaver.exe"


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
    """Entry point. Always exits 0 to avoid blocking session start.

    Decision tree:
      1. auto_launch_gui_on_session OFF       -> exit 0 (no-op)
      2. minimized=True (tray reminder mode)  -> if tray running, no-op;
                                                 else spawn `exe --tray`
      3. minimized=False (full window mode)   -> if GUI window already
                                                 running, no-op; else
                                                 spawn `exe` (full GUI)

    The tray and the GUI window have separate single-instance locks
    so they can coexist (tray is always-on indicator; GUI window is
    per-session reminder). Closing the GUI window releases its lock,
    so the next Claude Code session re-spawns the window.
    """
    prefs = Prefs.load()

    # Default-off gate. This launcher NEVER spawns anything unless the user
    # has explicitly opted in via prefs.auto_launch_gui_on_session (default
    # False). With it off — the shipping default — session start is a pure
    # no-op and no window or tray is forced onto the screen.
    if not prefs.auto_launch_gui_on_session:
        return 0

    # When opted in, minimized mode (the default once opt-in) launches only
    # the tray — no window. The full-window path below runs solely when the
    # user has ALSO turned auto_launch_minimized OFF, i.e. a deliberate
    # "open the window each session" choice. Even then, the GUI itself hides
    # to the tray on close/minimize and carries WS_EX_NOACTIVATE, so it
    # cannot steal keyboard focus.

    # Choose target based on mode.
    want_tray = prefs.auto_launch_minimized
    target_lock = _TRAY_INSTANCE_NAME if want_tray else _GUI_INSTANCE_NAME

    # Clear any stale pidfile from a previously crashed session before checking.
    cleared = _clear_stale_lock(target_lock)
    if cleared:
        _log_session(f"session_launcher: cleared stale lock for {target_lock}")

    # Skip if the requested target is genuinely already running.
    if is_locked(target_lock):
        _log_session("session_launcher: already running (pid+http alive), skip")
        return 0

    exe = _find_exe()
    if exe is None:
        # Frozen exe missing — fall back to running from source.
        py = sys.executable
        if sys.platform == "win32":
            cand = Path(py).with_name("pythonw.exe")
            if cand.is_file():
                py = str(cand)
        if want_tray:
            python_args = [py, "-m", "claude_backend", "tray"]
        else:
            python_args = [py, "-m", "claude_backend.gui"]
        spawned = _spawn_detached(python_args)
        _log_session(f"session_launcher: spawn(source)={'ok' if spawned else 'fail'} target={python_args[-1]}")
        if spawned:
            _verify_http_in_background()
        return 0

    args: list[str] = [str(exe)]
    if want_tray:
        args.append("--tray")
    spawned = _spawn_detached(args)
    _log_session(f"session_launcher: spawn(exe)={'ok' if spawned else 'fail'} path={exe}")
    if spawned:
        _verify_http_in_background()
    return 0


if __name__ == "__main__":
    sys.exit(main())

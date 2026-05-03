"""Single-instance enforcement for Token Saver tray + launcher.

Two layers:

1. **Windows named mutex** — primary mechanism on Windows. Uses
   `kernel32.CreateMutexW` with a global name. If the mutex already
   exists (`ERROR_ALREADY_EXISTS = 183`), another process owns it
   and we should not start a duplicate.

2. **PID lockfile fallback** — for non-Windows platforms or when
   ctypes is unavailable. Writes our PID to a lockfile, checks if
   any existing PID in the lockfile is still alive via psutil.

The mutex handle is held for the lifetime of the process; OS releases
it on exit. The PID lockfile is written/cleaned best-effort.

Usage:

    from claude_backend.single_instance import acquire_or_exit

    handle = acquire_or_exit("ClaudeTokenSaverTray")
    # ... rest of program; handle stays in scope
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Windows constant returned by GetLastError when CreateMutex finds an existing one.
_ERROR_ALREADY_EXISTS = 183


def _acquire_windows_mutex(name: str) -> tuple[bool, Any]:
    """Try to create a named mutex. Returns (acquired, handle).

    handle stays in scope for process lifetime to keep mutex alive.
    Caller should keep a reference even though handle is opaque.
    """
    try:
        import ctypes
        from ctypes import wintypes
    except ImportError:
        return False, None

    try:
        kernel32 = ctypes.windll.kernel32
        kernel32.CreateMutexW.argtypes = [
            wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR,
        ]
        kernel32.CreateMutexW.restype = wintypes.HANDLE

        # Prefix with "Local\" so the mutex is per-user-session, not global.
        # Avoids cross-user-session collisions on shared Windows machines.
        full_name = f"Local\\{name}"
        handle = kernel32.CreateMutexW(None, False, full_name)
        last_err = kernel32.GetLastError()
        if not handle:
            logger.debug("CreateMutexW returned NULL (err=%d)", last_err)
            return False, None
        if last_err == _ERROR_ALREADY_EXISTS:
            # Another process owns it. Close our handle to avoid leak.
            kernel32.CloseHandle(handle)
            return False, None
        return True, handle
    except Exception as e:
        logger.debug("Windows mutex path failed: %s", e)
        return False, None


def _pidfile_path(name: str) -> Path:
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)
    return Path.home() / ".claude" / f"{safe}.pid"


def _acquire_pidfile(name: str) -> tuple[bool, Path | None]:
    """PID lockfile fallback. Returns (acquired, pidfile_path)."""
    pidfile = _pidfile_path(name)
    pidfile.parent.mkdir(parents=True, exist_ok=True)

    # Check if existing PID in file is still alive.
    if pidfile.is_file():
        try:
            existing_pid = int(pidfile.read_text(encoding="utf-8").strip())
        except (ValueError, OSError):
            existing_pid = -1

        if existing_pid > 0:
            try:
                import psutil
                if psutil.pid_exists(existing_pid):
                    return False, pidfile
            except ImportError:
                # No psutil — assume stale; overwrite.
                pass

    # Claim the lockfile by writing our PID.
    try:
        pidfile.write_text(str(os.getpid()), encoding="utf-8")
        return True, pidfile
    except OSError as e:
        logger.warning("Cannot write PID lockfile %s: %s", pidfile, e)
        # Allow startup anyway — better to run than block on filesystem error.
        return True, None


def acquire_or_exit(name: str, exit_code: int = 0) -> Any:
    """Try to acquire a single-instance lock. Exit cleanly if already held.

    Returns an opaque handle (Windows mutex + pidfile, or pidfile alone).
    Caller must keep this in scope for the process lifetime — letting it
    be garbage-collected releases the mutex early.

    On Windows: tries named mutex first (primary enforcement). On success
    ALSO writes a PID lockfile so external processes can detect via
    `is_locked()` without needing to attempt mutex acquisition. If mutex
    creation fails entirely (rare), falls back to pidfile only.

    On other platforms: pidfile only.

    Exits the process via sys.exit if another instance is detected.
    """
    if sys.platform == "win32":
        ok, handle = _acquire_windows_mutex(name)
        if ok:
            # Mutex acquired; also write pidfile (advisory, for is_locked()).
            _acquire_pidfile(name)
            return handle
        if handle is None:
            # Mutex creation failed entirely — fall back to pidfile.
            ok2, pidfile = _acquire_pidfile(name)
            if ok2:
                return pidfile
        # Either mutex existed (another instance) or pidfile says alive.
        logger.info("Another instance of %s is already running; exiting.", name)
        sys.exit(exit_code)

    # Non-Windows path.
    ok, pidfile = _acquire_pidfile(name)
    if ok:
        return pidfile
    logger.info("Another instance of %s is already running; exiting.", name)
    sys.exit(exit_code)


def is_locked(name: str) -> bool:
    """Non-acquiring check: is another instance currently running?

    Used by the GUI to detect a running tray, e.g. for status display.
    Returns False on any error (don't false-positive).
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
        return bool(psutil.pid_exists(existing_pid))
    except ImportError:
        # Best effort — assume locked if pidfile exists with valid PID.
        return True

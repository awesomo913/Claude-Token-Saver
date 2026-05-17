# From: claude_backend/single_instance.py:240
# Non-acquiring check: is another instance currently running?

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

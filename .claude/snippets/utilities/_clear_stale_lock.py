# From: claude_backend/session_launcher.py:74
# Remove pidfile if the recorded PID is dead or reused by another process.

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

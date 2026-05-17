# From: claude_backend/single_instance.py:120
# PID lockfile fallback. Returns (acquired, pidfile_path).

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

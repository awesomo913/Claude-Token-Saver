# From: launch_token_saver.py:26
# Redirect None stdout/stderr (frozen --windowed) to a log file.

def _neutralize_none_streams() -> None:
    """Redirect None stdout/stderr (frozen --windowed) to a log file.

    Idempotent: a no-op when streams are already real (dev runs, console
    attached). Falls back to os.devnull if the log file can't be opened
    (read-only homedir, etc.) — never raises.

    Must be called BEFORE importing anything that might log on import.
    """
    if sys.stdout is not None and sys.stderr is not None:
        return
    log_path = Path.home() / ".claude" / "token_saver_console.log"
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        # line-buffered append so multiple subprocesses can interleave safely
        sink = open(log_path, "a", encoding="utf-8", buffering=1)
    except OSError:
        sink = open(os.devnull, "w", encoding="utf-8")
    if sys.stdout is None:
        sys.stdout = sink
    if sys.stderr is None:
        sys.stderr = sink

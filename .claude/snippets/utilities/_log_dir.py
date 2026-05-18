# From: claude_backend/diagnostics_logger.py:32
# Return today's log dir, with two fallbacks before giving up.

def _log_dir() -> Path:
    """Return today's log dir, with two fallbacks before giving up.

    Frozen --windowed exes have `sys.stderr is None`, so any unhandled
    OSError here would crash bootstrap() before `_INITIALIZED=True`,
    skipping the excepthook install and losing the process silently.
    Each level is wrapped to ensure bootstrap always returns *some*
    writable Path: %HOME/.claude/session-data/<date>, then
    %TEMP/.claude_logs/<date>, then cwd as last resort.
    """
    today = _dt.date.today().isoformat()
    primary = Path.home() / ".claude" / "session-data" / today
    try:
        primary.mkdir(parents=True, exist_ok=True)
        probe = primary / ".write_probe"
        probe.touch()
        probe.unlink()
        return primary
    except OSError:
        pass

    fallback = Path(os.environ.get("TEMP",
                                   os.environ.get("TMP", "."))) / \
               ".claude_logs" / today
    try:
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback
    except OSError:
        # Last resort: cwd. If THIS fails the disk is unusable; let the
        # caller's bare except in bootstrap absorb it rather than crash.
        return Path(".")

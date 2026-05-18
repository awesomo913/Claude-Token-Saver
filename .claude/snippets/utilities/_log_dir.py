# From: claude_backend/diagnostics_logger.py:32
# Return today's log dir, with fallback to %TEMP% if home is unwritable.

def _log_dir() -> Path:
    """Return today's log dir, with fallback to %TEMP% if home is unwritable."""
    today = _dt.date.today().isoformat()
    primary = Path.home() / ".claude" / "session-data" / today
    try:
        primary.mkdir(parents=True, exist_ok=True)
        probe = primary / ".write_probe"
        probe.touch()
        probe.unlink()
        return primary
    except OSError:
        fallback = Path(os.environ.get("TEMP",
                                       os.environ.get("TMP", "."))) / \
                   ".claude_logs" / today
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback

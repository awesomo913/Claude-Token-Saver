# From: claude_backend/session_launcher.py:46
# Append one timestamped line to today's session log. Never raises.

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

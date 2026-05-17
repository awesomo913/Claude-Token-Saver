# From: launch_token_saver.py:75
# Write traceback to ~/.claude/token_saver_crash.log. Best-effort.

def _log_crash(exc: BaseException) -> Path | None:
    """Write traceback to ~/.claude/token_saver_crash.log. Best-effort.

    Returns the log path if written, else None.
    """
    try:
        log_path = Path.home() / ".claude" / "token_saver_crash.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().isoformat(timespec="seconds")
        mode = "tray" if _is_tray_mode() else "gui"
        with log_path.open("a", encoding="utf-8") as f:
            f.write(f"\n=== {ts} (mode={mode}) ===\n")
            f.write(f"argv: {sys.argv}\n")
            traceback.print_exception(type(exc), exc, exc.__traceback__, file=f)
        return log_path
    except Exception:
        # Never let crash logging itself crash the exit path.
        return None

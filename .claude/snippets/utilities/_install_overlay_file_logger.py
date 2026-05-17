# From: claude_backend/overlay.py:679
# Mirror overlay's logger to ~/.claude/session-data/<date>/exe_Overlay.log.

def _install_overlay_file_logger() -> None:
    """Mirror overlay's logger to ~/.claude/session-data/<date>/exe_Overlay.log.

    Frozen exe has no console, so warnings vanished into the void. The file
    handler is best-effort: any failure here is silent (logged at debug
    via the existing logger config) since we don't want logging setup to
    crash the overlay process.
    """
    try:
        from datetime import date
        log_dir = Path.home() / ".claude" / "session-data" / date.today().isoformat()
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / "exe_Overlay.log"
        fh = logging.FileHandler(log_path, encoding="utf-8")
        fh.setLevel(logging.INFO)
        fh.setFormatter(logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s: %(message)s",
        ))
        logging.getLogger().addHandler(fh)
        logger.info("overlay logger attached to %s", log_path)
    except Exception as e:
        logger.debug("overlay file logger install failed: %s", e)

# From: claude_backend/auto_inject.py:132
# Timestamped copy of settings.json. Returns path on success, None on fail.

def _make_backup() -> Path | None:
    """Timestamped copy of settings.json. Returns path on success, None on fail."""
    backup = SETTINGS_PATH.with_suffix(
        f".json.backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    )
    try:
        shutil.copy2(SETTINGS_PATH, backup)
        return backup
    except OSError as e:
        logger.warning("Backup failed: %s", e)
        return None

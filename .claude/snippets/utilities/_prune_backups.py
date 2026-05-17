# From: claude_backend/auto_inject.py:115
# Keep only the newest `keep` backups; unlink the rest. Best-effort.

def _prune_backups(keep: int = _BACKUP_KEEP) -> None:
    """Keep only the newest `keep` backups; unlink the rest. Best-effort."""
    try:
        backups = sorted(
            SETTINGS_PATH.parent.glob("settings.json.backup-*"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
    except OSError:
        return
    for old in backups[keep:]:
        try:
            old.unlink()
        except OSError as e:
            logger.debug("Failed to prune backup %s: %s", old, e)

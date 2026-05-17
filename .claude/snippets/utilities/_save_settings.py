# From: claude_backend/auto_inject.py:159
# Backup, write atomically, prune old backups. Returns (ok, message).

def _save_settings(data: dict) -> tuple[bool, str]:
    """Backup, write atomically, prune old backups. Returns (ok, message)."""
    backup = _make_backup()
    try:
        new_text = json.dumps(data, indent=2, ensure_ascii=False)
        _atomic_write_text(SETTINGS_PATH, new_text)
    except OSError as e:
        if backup is not None:
            try:
                shutil.copy2(backup, SETTINGS_PATH)
            except OSError:
                pass
        return False, f"Cannot write settings.json: {e}"
    _prune_backups()
    msg = f"Backup saved at {backup.name}" if backup else "Wrote (no backup made)"
    return True, msg

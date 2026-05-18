# From: claude_backend/tray.py:70
# Snooze flag honored only if timestamp is in future.

def _is_snoozed() -> bool:
    """Snooze flag honored only if timestamp is in future."""
    if not SNOOZE_FILE.is_file():
        return False
    try:
        until = float(SNOOZE_FILE.read_text().strip())
        return time.time() < until
    except (ValueError, OSError):
        return False

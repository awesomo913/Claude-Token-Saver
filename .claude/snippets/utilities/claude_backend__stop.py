# From: claude_backend/hotkey.py:183
# Unregister the hotkey. Idempotent.

def stop() -> None:
    """Unregister the hotkey. Idempotent."""
    global _registered_combo, _thread
    with _lock:
        if keyboard is not None and _registered_combo:
            try:
                keyboard.remove_hotkey(_registered_combo)
            except Exception as e:
                logger.debug("Failed to remove hotkey: %s", e)
        _registered_combo = None

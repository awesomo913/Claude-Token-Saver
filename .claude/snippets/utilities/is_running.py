# From: claude_backend/hotkey.py:196
# True if hotkey is currently registered.

def is_running() -> bool:
    """True if hotkey is currently registered."""
    return _registered_combo is not None and _thread is not None and _thread.is_alive()

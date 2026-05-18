# From: claude_backend/hotkey.py:122
# Register the global hotkey. Returns True on success.

def start(combo: str | None = None) -> bool:
    """Register the global hotkey. Returns True on success.

    Idempotent: re-registers if combo changed; no-op if same combo
    already active.
    """
    global _thread, _registered_combo

    if keyboard is None:
        logger.warning("keyboard library not available; hotkey disabled")
        return False

    with _lock:
        if combo is None:
            combo = Prefs.load().hotkey_combo

        if _registered_combo == combo and _thread is not None and _thread.is_alive():
            return True  # already running with same combo

        # Tear down existing registration if any
        try:
            if _registered_combo:
                keyboard.remove_hotkey(_registered_combo)
        except Exception as e:
            logger.debug("Failed to remove old hotkey: %s", e)

        try:
            keyboard.add_hotkey(combo, _on_hotkey, suppress=False)
        except Exception as e:
            logger.warning(
                "Hotkey registration failed for '%s': %s. "
                "On corporate Windows this can require admin rights.",
                combo, e,
            )
            return False

        _registered_combo = combo

        # Spawn a daemon thread that just keeps the hook alive.
        # `keyboard.add_hotkey` already sets up the OS-level hook; we
        # just need a thread to track 'aliveness' for status reporting.
        if _thread is None or not _thread.is_alive():
            _thread = threading.Thread(
                target=_keep_alive, name="token_saver_hotkey", daemon=True,
            )
            _thread.start()

        logger.info("Hotkey '%s' registered", combo)
        return True

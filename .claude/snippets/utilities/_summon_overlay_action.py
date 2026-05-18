# From: claude_backend/tray.py:185
# Tray-menu handler — spawns overlay or raises existing one via IPC.

def _summon_overlay_action(icon: "pystray.Icon") -> None:
    """Tray-menu handler — spawns overlay or raises existing one via IPC."""
    try:
        _spawn_overlay_subprocess()
        icon.notify("Improve overlay summoned", "Look for the floating pill")
    except Exception as e:
        logger.exception("Summon overlay (tray menu) failed")
        icon.notify("Summon failed", str(e))

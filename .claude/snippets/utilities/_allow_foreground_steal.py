# From: claude_backend/http_server.py:432
# Grant any process permission to call SetForegroundWindow.

def _allow_foreground_steal() -> None:
    """Grant any process permission to call SetForegroundWindow.

    The HTTP server runs in the tray process; the GUI is a separate
    process. Windows blocks SetForegroundWindow from a non-foreground
    process, which is why `lift() + focus_force()` from the GUI
    sometimes only blinks the taskbar instead of surfacing the window.
    Calling AllowSetForegroundWindow(ASFW_ANY) hands the foreground
    privilege to whichever process tries to claim it next — typically
    the GUI when it picks up the pending file. No-op on non-Windows
    or when ctypes/user32 is unavailable.
    """
    if sys.platform != "win32":
        return
    try:
        import ctypes
        ctypes.windll.user32.AllowSetForegroundWindow(-1)  # ASFW_ANY
    except Exception as e:
        logger.debug("AllowSetForegroundWindow failed: %s", e)

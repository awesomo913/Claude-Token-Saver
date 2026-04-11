# From: browser_actions.py:59
# Bring a window to the foreground.

def focus_window(hwnd: int) -> bool:
    """Bring a window to the foreground."""
    try:
        user32 = ctypes.windll.user32
        if not user32.IsWindow(hwnd):
            logger.error("Window %d no longer exists", hwnd)
            return False
        user32.ShowWindow(hwnd, 9)  # SW_RESTORE
        user32.SetForegroundWindow(hwnd)
        time.sleep(0.3)
        return True
    except Exception as e:
        logger.error("Failed to focus window %d: %s", hwnd, e)
        return False

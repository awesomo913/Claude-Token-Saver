# From: window_manager.py:112
# Move and resize a window by its handle.

def move_window(hwnd: int, rect: WindowRect) -> bool:
    """Move and resize a window by its handle."""
    if not WIN32_AVAILABLE:
        return False
    try:
        user32 = ctypes.windll.user32
        user32.ShowWindow(hwnd, 9)  # SW_RESTORE
        time.sleep(0.1)
        result = user32.MoveWindow(hwnd, rect.x, rect.y, rect.width, rect.height, True)
        return bool(result)
    except Exception as e:
        logger.error("Failed to move window: %s", e)
        return False

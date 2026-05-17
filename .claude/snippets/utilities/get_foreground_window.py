# From: window_manager.py:270
# Get the currently focused/foreground window handle.

def get_foreground_window() -> Optional[int]:
    """Get the currently focused/foreground window handle."""
    if not WIN32_AVAILABLE:
        return None
    try:
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        if hwnd and ctypes.windll.user32.IsWindow(hwnd):
            return hwnd
    except Exception:
        pass
    return None

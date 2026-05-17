# From: window_manager.py:283
# Get a window's title by handle.

def get_window_title(hwnd: int) -> str:
    """Get a window's title by handle."""
    if not WIN32_AVAILABLE:
        return ""
    try:
        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(length + 1)
        ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
        return buf.value
    except Exception:
        return ""

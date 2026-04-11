# From: browser_actions.py:48
# Read window title via Win32. Zero impact.

def _get_window_title(hwnd: int) -> str:
    """Read window title via Win32. Zero impact."""
    try:
        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(length + 1)
        ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
        return buf.value
    except Exception:
        return ""

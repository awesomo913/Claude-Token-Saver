# From: browser_actions.py:75
# Get window position (left, top, right, bottom).

def get_window_rect(hwnd: int) -> Optional[tuple[int, int, int, int]]:
    """Get window position (left, top, right, bottom)."""
    try:
        rect = ctypes.wintypes.RECT()
        ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
        return (rect.left, rect.top, rect.right, rect.bottom)
    except Exception:
        return None

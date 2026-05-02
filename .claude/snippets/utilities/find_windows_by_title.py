# From: window_manager.py:75
# Find ALL visible windows whose title contains the pattern (case-insensitive).

def find_windows_by_title(pattern: str) -> list[int]:
    """Find ALL visible windows whose title contains the pattern (case-insensitive).

    Works with Chrome, Edge, Firefox, Electron apps, native apps — any window.
    No class name filtering, so it catches everything.
    """
    if not WIN32_AVAILABLE or not pattern:
        return []

    pattern_lower = pattern.lower()
    handles = []
    user32 = ctypes.windll.user32

    def enum_callback(hwnd, _):
        if user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buf = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buf, length + 1)
                if pattern_lower in buf.value.lower():
                    handles.append(hwnd)
        return True

    WNDENUMPROC = ctypes.WINFUNCTYPE(
        ctypes.c_bool, ctypes.c_int, ctypes.POINTER(ctypes.c_int)
    )
    user32.EnumWindows(WNDENUMPROC(enum_callback), 0)
    return handles

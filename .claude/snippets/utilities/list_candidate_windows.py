# From: window_manager.py:314
# List all visible windows that could be AI chat interfaces.

def list_candidate_windows() -> list[tuple[int, str, str]]:
    """List all visible windows that could be AI chat interfaces.

    Returns [(hwnd, class_name, title), ...] for windows that look
    like browsers or chat apps (not system windows).
    """
    if not WIN32_AVAILABLE:
        return []

    results = []
    user32 = ctypes.windll.user32
    # Window classes that are likely AI chat candidates
    good_classes = {"Chrome_WidgetWin_1", "MozillaWindowClass", "CabinetWClass",
                    "ApplicationFrameWindow", "CASCADIA_HOSTING_WINDOW_CLASS",
                    "Electron", "TkTopLevel"}
    skip_titles = {"program manager", "settings", "nvidia", "app center",
                   "file explorer", "task manager"}

    def enum_cb(hwnd, _):
        if user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 5:
                buf = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buf, length + 1)
                title = buf.value
                cls = ctypes.create_unicode_buffer(256)
                user32.GetClassNameW(hwnd, cls, 256)
                class_name = cls.value

                title_lower = title.lower()
                if not any(s in title_lower for s in skip_titles):
                    results.append((hwnd, class_name, title))
        return True

    WNDENUMPROC = ctypes.WINFUNCTYPE(
        ctypes.c_bool, ctypes.c_int, ctypes.POINTER(ctypes.c_int)
    )
    user32.EnumWindows(WNDENUMPROC(enum_cb), 0)
    return results

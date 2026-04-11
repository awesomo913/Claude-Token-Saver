# From: browser_actions.py:193
# Check if the window is a terminal (CMD, PowerShell, Windows Terminal).

def _is_terminal_window(hwnd: int) -> bool:
    """Check if the window is a terminal (CMD, PowerShell, Windows Terminal)."""
    try:
        cls = ctypes.create_unicode_buffer(256)
        ctypes.windll.user32.GetClassNameW(hwnd, cls, 256)
        terminal_classes = {"ConsoleWindowClass", "CASCADIA_HOSTING_WINDOW_CLASS",
                           "PseudoConsoleWindow", "mintty"}
        return cls.value in terminal_classes
    except Exception:
        return False

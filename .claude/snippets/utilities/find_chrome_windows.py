# From: window_manager.py:105
# Backward compat: find Chrome windows.

def find_chrome_windows() -> list[int]:
    """Backward compat: find Chrome windows."""
    return find_windows_by_title("chrome")

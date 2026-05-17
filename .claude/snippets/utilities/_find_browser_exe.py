# From: window_manager.py:169
# Find a browser executable on disk.

def _find_browser_exe(browser: str) -> Optional[str]:
    """Find a browser executable on disk."""
    if browser == "any":
        # Try Chrome first, then Edge, then Firefox
        for b in ["chrome", "edge", "firefox"]:
            exe = _find_browser_exe(b)
            if exe:
                return exe
        return None

    paths = BROWSER_PATHS.get(browser, [])
    for path in paths:
        if os.path.exists(path):
            return path
    return None

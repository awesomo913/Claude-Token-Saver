# From: window_manager.py:40
# Get primary monitor resolution.

def get_screen_size() -> ScreenInfo:
    """Get primary monitor resolution."""
    if WIN32_AVAILABLE:
        user32 = ctypes.windll.user32
        return ScreenInfo(
            width=user32.GetSystemMetrics(0),
            height=user32.GetSystemMetrics(1),
        )
    return ScreenInfo(width=1920, height=1080)

# From: window_manager.py:296
# Wait for user to click a window, then capture and position it.

def capture_foreground_and_position(corner: str, delay: float = 3.0) -> Optional[tuple[int, str]]:
    """Wait for user to click a window, then capture and position it.

    Returns (hwnd, window_title) or None. The delay gives the user time
    to click the target window.
    """
    time.sleep(delay)
    hwnd = get_foreground_window()
    if not hwnd:
        return None

    title = get_window_title(hwnd)
    rect = get_quarter_rect(corner)
    move_window(hwnd, rect)
    logger.info("Captured window '%s' (hwnd=%d) to %s", title[:60], hwnd, corner)
    return (hwnd, title)

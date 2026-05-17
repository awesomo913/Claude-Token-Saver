# From: window_manager.py:133
# Find a window by title pattern and move it to the given corner.

def find_and_position_window(title_pattern: str, corner: str) -> Optional[int]:
    """Find a window by title pattern and move it to the given corner.

    Returns the hwnd if found and positioned, None otherwise.
    """
    handles = find_windows_by_title(title_pattern)
    if not handles:
        return None

    hwnd = handles[0]
    rect = get_quarter_rect(corner)
    move_window(hwnd, rect)
    logger.info("Found and positioned '%s' window (hwnd=%d) to %s",
                title_pattern, hwnd, corner)
    return hwnd

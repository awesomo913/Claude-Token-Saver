# From: window_manager.py:127
# Reposition an existing window to a quarter of the screen.

def position_existing_window(hwnd: int, corner: str = "bottom-right") -> bool:
    """Reposition an existing window to a quarter of the screen."""
    rect = get_quarter_rect(corner)
    return move_window(hwnd, rect)

# From: window_manager.py:51
# Get a 1/4 screen rectangle for a given corner.

def get_quarter_rect(
    corner: str = "bottom-right",
    screen: Optional[ScreenInfo] = None,
    taskbar_height: int = 48,
) -> WindowRect:
    """Get a 1/4 screen rectangle for a given corner."""
    if screen is None:
        screen = get_screen_size()

    hw = screen.width // 2
    hh = (screen.height - taskbar_height) // 2

    positions = {
        "top-left": WindowRect(0, 0, hw, hh),
        "top-right": WindowRect(hw, 0, hw, hh),
        "bottom-left": WindowRect(0, hh, hw, hh),
        "bottom-right": WindowRect(hw, hh, hw, hh),
    }

    return positions.get(corner, positions["bottom-right"])

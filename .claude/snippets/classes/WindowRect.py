# From: window_manager.py:24
# Screen rectangle.

@dataclass
class WindowRect:
    """Screen rectangle."""
    x: int
    y: int
    width: int
    height: int

# From: ai_profiles.py:17

@dataclass
class AIProfile:
    """Describes how to automate a specific AI web chat."""
    name: str = "Custom"
    title_pattern: str = ""             # Window title substring (case-insensitive)
    url_pattern: str = ""               # URL substring for CDP tab matching
    input_offset_from_bottom: int = 80  # Pixels from window bottom to input center
    send_method: str = "enter"          # "enter" or "click_button"
    send_button_right_offset: int = 60  # Pixels from right edge (for click_button)
    send_button_bottom_offset: int = 80 # Pixels from bottom (for click_button)
    wait_multiplier: float = 1.0        # Scales all wait times (1.0=normal, 2.0=double)
    read_click_fraction: float = 0.33   # Where to click before Ctrl+A (fraction from top)
    url: str = ""                       # URL to launch (empty = find existing window)
    browser: str = "any"                # "chrome", "edge", "firefox", "any"
    notes: str = ""                     # Help text about quirks

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "AIProfile":
        known = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in known}
        return cls(**filtered)

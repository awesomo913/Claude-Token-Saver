# From: claude_backend/prefs.py:54

    def __post_init__(self) -> None:
        # Mutable defaults for dataclass fields must be created lazily.
        if self.overlay_position is None:
            self.overlay_position = [0, 0]

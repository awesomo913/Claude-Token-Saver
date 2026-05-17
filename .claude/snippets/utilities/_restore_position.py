# From: claude_backend/overlay.py:139
# Get saved position or default to top-right of primary monitor.

    def _restore_position(self) -> tuple[int, int]:
        """Get saved position or default to top-right of primary monitor."""
        pos = self._prefs.overlay_position or [0, 0]
        if pos and pos != [0, 0]:
            return int(pos[0]), int(pos[1])
        # Default: top-right corner with 24px margin
        try:
            sw = self.winfo_screenwidth()
            return sw - _OVERLAY_W - 24, 24
        except Exception:
            return 100, 100

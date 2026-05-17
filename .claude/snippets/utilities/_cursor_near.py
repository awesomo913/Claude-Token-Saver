# From: claude_backend/overlay.py:229
# True if the global mouse cursor is within FADE_PROXIMITY_PX

    def _cursor_near(self) -> bool:
        """True if the global mouse cursor is within FADE_PROXIMITY_PX
        of the overlay's bounds. Uses winfo_pointer{x,y} which works
        even though our window is overrideredirect."""
        try:
            mx = self.winfo_pointerx()
            my = self.winfo_pointery()
            x = self.winfo_x()
            y = self.winfo_y()
            w = self.winfo_width() or _OVERLAY_W
            h = self.winfo_height() or _OVERLAY_H
        except Exception:  # noqa: BLE001
            return False
        # Distance to nearest edge of the rect.
        dx = max(x - mx, 0, mx - (x + w))
        dy = max(y - my, 0, my - (y + h))
        return (dx * dx + dy * dy) <= (_FADE_PROXIMITY_PX * _FADE_PROXIMITY_PX)

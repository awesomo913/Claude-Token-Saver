# From: claude_backend/overlay.py:186
# Persist current position to prefs.

    def _save_position(self) -> None:
        """Persist current position to prefs."""
        try:
            x = self.winfo_x()
            y = self.winfo_y()
            self._prefs.overlay_position = [x, y]
            self._prefs.save()
        except Exception as e:
            logger.debug("Failed to save overlay position: %s", e)

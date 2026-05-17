# From: claude_backend/gui.py:3076
# Stop the periodic refresh tick if it's scheduled.

    def _cancel_settings_refresh(self) -> None:
        """Stop the periodic refresh tick if it's scheduled."""
        if self._settings_refresh_id is not None:
            try:
                self.after_cancel(self._settings_refresh_id)
            except Exception:
                pass
            self._settings_refresh_id = None

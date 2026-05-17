# From: claude_backend/gui.py:2884
# Sub-toggle: persist 'open minimized to tray' preference.

    def _al_toggle_minimized(self) -> None:
        """Sub-toggle: persist 'open minimized to tray' preference."""
        self._prefs.auto_launch_minimized = bool(self._set_auto_launch_min.get())
        if not self._prefs.save():
            self._toast("Failed to save preference", "warning")
            return
        mode = "tray" if self._prefs.auto_launch_minimized else "full window"
        self._toast(f"Auto-launch mode: {mode}", "info")

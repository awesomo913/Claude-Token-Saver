# From: claude_backend/gui.py:2790
# Persist 'show welcome on launch' checkbox state.

    def _save_welcome_pref(self) -> None:
        """Persist 'show welcome on launch' checkbox state."""
        self._prefs.show_welcome_on_launch = bool(self._set_show_welcome.get())
        if self._prefs.save():
            state = "ON" if self._prefs.show_welcome_on_launch else "OFF"
            self._toast(f"Welcome on launch: {state}", "info")
        else:
            self._toast("Failed to save preference", "warning")

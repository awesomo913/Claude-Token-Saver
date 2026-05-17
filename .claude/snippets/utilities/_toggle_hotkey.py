# From: claude_backend/gui.py:3312
# Persist pref, register/unregister hotkey IF we own a hotkey daemon

    def _toggle_hotkey(self) -> None:
        """Persist pref, register/unregister hotkey IF we own a hotkey daemon
        in this process (we don't — it's in tray). Pref change requires tray
        restart to pick up.
        """
        on = bool(self._set_hotkey.get())
        self._prefs.enable_hotkey = on
        if not self._prefs.save():
            self._toast("Failed to save preference", "warning")
            return
        self._toast(
            f"Hotkey: {'ON' if on else 'OFF'} (restart tray to apply)",
            "info" if on else "warning",
        )
        self._refresh_backend_statuses()

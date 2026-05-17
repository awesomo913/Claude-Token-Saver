# From: claude_backend/gui.py:3034
# Delete the Startup shortcut. Tray + auto-inject hook unaffected.

    def _remove_autostart(self) -> None:
        """Delete the Startup shortcut. Tray + auto-inject hook unaffected."""
        lnk_path = self._autostart_shortcut_path()
        if not lnk_path.is_file():
            self._toast("Shortcut already absent", "info")
            self._refresh_autostart_status()
            return
        try:
            lnk_path.unlink()
            self._toast("Autostart shortcut removed", "info")
        except OSError as e:
            self._toast(f"Remove failed: {e}", "error")
        self._refresh_autostart_status()

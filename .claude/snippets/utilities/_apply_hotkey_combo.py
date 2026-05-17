# From: claude_backend/gui.py:3328
# Save typed combo to prefs.

    def _apply_hotkey_combo(self) -> None:
        """Save typed combo to prefs."""
        combo = self._hk_combo_entry.get().strip()
        if not combo:
            self._toast("Empty combo not allowed", "warning")
            return
        self._prefs.hotkey_combo = combo
        if self._prefs.save():
            self._toast(f"Hotkey combo saved: {combo} (restart tray to apply)",
                        "info")
        self._refresh_backend_statuses()

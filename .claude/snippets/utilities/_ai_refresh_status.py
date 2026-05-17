# From: claude_backend/gui.py:2739
# Check and display auto-inject install status.

    def _ai_refresh_status(self) -> None:
        """Check and display auto-inject install status."""
        try:
            from . import auto_inject
        except Exception as e:
            self._ai_status_lbl.configure(text=f"Module error: {e}", text_color=C["err"])
            return
        s = auto_inject.check_status()
        if not s["settings_exists"]:
            self._ai_status_lbl.configure(text="settings.json missing", text_color=C["err"])
            self._ai_install_btn.configure(state="disabled")
        elif not s["settings_valid"]:
            self._ai_status_lbl.configure(text=f"settings.json INVALID JSON", text_color=C["err"])
            self._ai_install_btn.configure(state="disabled")
        elif s["installed"]:
            self._ai_status_lbl.configure(text="INSTALLED — running on every session",
                                          text_color=C["ok"])
            self._ai_install_btn.configure(state="disabled")
            self._ai_uninstall_btn.configure(state="normal")
        else:
            self._ai_status_lbl.configure(text="Not installed", text_color=C["fg3"])
            self._ai_install_btn.configure(state="normal")
            self._ai_uninstall_btn.configure(state="disabled")

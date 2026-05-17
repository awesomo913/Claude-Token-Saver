# From: claude_backend/gui.py:380
# Open welcome dialog. Reuses existing window if already open.

    def _open_welcome(self) -> None:
        """Open welcome dialog. Reuses existing window if already open."""
        if self._welcome_dlg is not None and self._welcome_dlg.winfo_exists():
            self._welcome_dlg.lift()
            self._welcome_dlg.focus_force()
            return

        def _on_install_done() -> None:
            # Refresh Settings tab status if user installed from welcome
            if hasattr(self, "_ai_status_lbl"):
                self._ai_refresh_status()
            self._toast("Auto-Inject installed", "success")

        try:
            self._welcome_dlg = show_welcome(
                self, self._prefs, on_install_callback=_on_install_done,
            )
        except Exception as e:
            logger.exception("Failed to open welcome dialog")
            self._toast(f"Welcome dialog failed: {e}", "error")

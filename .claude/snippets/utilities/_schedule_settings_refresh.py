# From: claude_backend/gui.py:3050
# Re-run backend status checks every 3s while Settings is visible.

    def _schedule_settings_refresh(self) -> None:
        """Re-run backend status checks every 3s while Settings is visible.

        Catches subprocess state changes (overlay/hotkey starting up after
        the user clicked a toggle) without requiring tab switches. Cancelled
        the moment the user leaves Settings to avoid wasted polls.
        """
        # Cancel any prior scheduled refresh first to avoid duplicates.
        self._cancel_settings_refresh()

        def _tick() -> None:
            try:
                if hasattr(self, "_bk_status_lbl"):
                    self._refresh_backend_statuses()
            except Exception as e:
                logger.debug("Settings refresh tick failed: %s", e)
            # Re-arm only if Settings is still the active view.
            current = next(
                (k for k, v in self._views.items() if v.winfo_ismapped()),
                None,
            )
            if current == "settings":
                self._settings_refresh_id = self.after(3000, _tick)

        self._settings_refresh_id = self.after(3000, _tick)

# From: claude_backend/welcome.py:292
# One-click install button inside welcome.

    def _do_install(self) -> None:
        """One-click install button inside welcome."""
        ok, msg = ai_install()
        if ok:
            self._refresh_status()
            if self._on_install:
                try:
                    self._on_install()
                except Exception as e:
                    logger.debug("install callback failed: %s", e)
        else:
            self._status_detail.configure(text=f"Install failed: {msg}",
                                          text_color=_C["err"])

# From: claude_backend/gui.py:710
# Check for HTTP-driven improve requests every second.

    def _poll_pending_file(self) -> None:
        """Check for HTTP-driven improve requests every second.

        The HTTP server (running in the tray process) writes a JSON
        payload to ~/.claude/token_saver_pending.json when a browser
        extension / overlay / hotkey fires /improve. We pick it up here,
        populate the Builder, and raise the window.
        """
        try:
            from .http_server import PENDING_PATH
            if PENDING_PATH.is_file():
                self._handle_pending(PENDING_PATH)
        except Exception as e:
            logger.debug("Pending poll error: %s", e)
        finally:
            # Re-arm; 1s cadence is fine — file appearance is rare.
            self.after(1000, self._poll_pending_file)

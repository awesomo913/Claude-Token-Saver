# From: claude_backend/gui.py:3226
# Kill any running --tray ClaudeTokenSaver process.

    def _close_tray(self) -> None:
        """Kill any running --tray ClaudeTokenSaver process."""
        killed = self._kill_processes_by_arg("--tray")
        if killed:
            self._toast(f"Tray closed ({killed} process)", "success")
        else:
            self._toast("No tray process found", "warning")
        try:
            self._refresh_backend_statuses()
        except Exception as e:
            logger.debug("status refresh after close_tray failed: %s", e)

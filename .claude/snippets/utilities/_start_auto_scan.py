# From: claude_backend/gui.py:1870
# Start the 5-minute auto-refresh cycle.

    def _start_auto_scan(self) -> None:
        """Start the 5-minute auto-refresh cycle."""
        self._stop_auto_scan()
        self._auto_scan_tick()

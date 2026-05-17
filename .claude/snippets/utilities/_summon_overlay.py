# From: claude_backend/gui.py:3259
# Spawn overlay subprocess (or raise existing one via IPC).

    def _summon_overlay(self) -> None:
        """Spawn overlay subprocess (or raise existing one via IPC).

        Works whether overlay is currently running or not — single_instance
        lock in overlay.main() handles the dup-launch case by writing a
        raise-flag the existing process polls every 1.5s.
        """
        try:
            from .tray import _spawn_overlay_subprocess
            _spawn_overlay_subprocess()
            self._toast("Overlay summoned", "success")
        except Exception as e:
            logger.exception("Summon overlay failed")
            self._toast(f"Summon failed: {e}", "error")
        # Reflect new state in the status row beside the toggle.
        try:
            self._refresh_backend_statuses()
        except Exception as e:
            logger.debug("backend status refresh failed: %s", e)

# From: claude_backend/gui.py:3238
# Kill running tray + spawn a fresh one (picks up newest exe).

    def _relaunch_tray(self) -> None:
        """Kill running tray + spawn a fresh one (picks up newest exe)."""
        killed = self._kill_processes_by_arg("--tray")
        # Brief settle so PyInstaller-bundled child cleanup completes
        # before re-spawn — otherwise the new tray may race the
        # single-instance lock release of the killed one and exit.
        self.after(800, self._relaunch_tray_phase2,
                   killed)

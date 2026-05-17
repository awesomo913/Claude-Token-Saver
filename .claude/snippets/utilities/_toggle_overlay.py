# From: claude_backend/gui.py:3279
# Persist pref, spawn/kill overlay subprocess to match.

    def _toggle_overlay(self) -> None:
        """Persist pref, spawn/kill overlay subprocess to match."""
        on = bool(self._set_overlay.get())
        self._prefs.show_overlay = on
        if not self._prefs.save():
            self._toast("Failed to save preference", "warning")
            return
        # We can spawn the overlay but we can't kill it cleanly from here
        # (it's in another process). User must restart tray to pick up "off".
        if on:
            try:
                import subprocess
                exe_path = (Path.home() / "Desktop" / "My Apps"
                            / "ClaudeTokenSaver" / "ClaudeTokenSaver.exe")
                if exe_path.is_file():
                    args = [str(exe_path), "--overlay"]
                else:
                    args = [sys.executable, "-m", "claude_backend.overlay"]
                creationflags = 0
                if sys.platform == "win32":
                    creationflags = (subprocess.CREATE_NO_WINDOW
                                     | subprocess.DETACHED_PROCESS)
                subprocess.Popen(args, creationflags=creationflags, close_fds=True)
                self._toast("Overlay started", "success")
            except Exception as e:
                self._toast(f"Overlay spawn failed: {e}", "error")
        else:
            self._toast(
                "Overlay will exit on next tray restart (or close it via right-click in dev)",
                "info",
            )
        self._refresh_backend_statuses()

# From: claude_backend/gui.py:3205
# Spawn a detached tray subprocess. Returns True on launch attempt.

    def _spawn_tray(self) -> bool:
        """Spawn a detached tray subprocess. Returns True on launch attempt."""
        try:
            import subprocess
            exe_path = (Path.home() / "Desktop" / "My Apps"
                        / "ClaudeTokenSaver" / "ClaudeTokenSaver.exe")
            if exe_path.is_file():
                args = [str(exe_path), "--tray"]
            else:
                args = [sys.executable, "-m", "claude_backend", "tray"]
            creationflags = 0
            if sys.platform == "win32":
                creationflags = (subprocess.CREATE_NO_WINDOW
                                 | subprocess.DETACHED_PROCESS)
            subprocess.Popen(args, creationflags=creationflags, close_fds=True)
            return True
        except Exception as e:
            logger.exception("Tray spawn failed")
            self._toast(f"Tray spawn failed: {e}", "error")
            return False

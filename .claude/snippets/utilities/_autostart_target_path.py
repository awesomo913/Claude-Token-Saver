# From: claude_backend/gui.py:2949
# Where the deployed exe is expected. Used as the shortcut target.

    def _autostart_target_path(self) -> Path:
        """Where the deployed exe is expected. Used as the shortcut target."""
        return Path.home() / "Desktop" / "My Apps" / "ClaudeTokenSaver" / "ClaudeTokenSaver.exe"

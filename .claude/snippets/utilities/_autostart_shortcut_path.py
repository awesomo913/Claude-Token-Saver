# From: claude_backend/gui.py:2940
# Resolve %APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\...

    def _autostart_shortcut_path(self) -> Path:
        """Resolve %APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Startup\\..."""
        import os
        appdata = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
        return (
            Path(appdata) / "Microsoft" / "Windows" / "Start Menu"
            / "Programs" / "Startup" / "ClaudeTokenSaverTray.lnk"
        )

# From: claude_backend/gui.py:2972
# Create or recreate the Startup shortcut pointing at current exe.

    def _repair_autostart(self) -> None:
        """Create or recreate the Startup shortcut pointing at current exe."""
        if sys.platform != "win32":
            self._toast("Autostart shortcut is Windows-only", "warning")
            return
        target = self._autostart_target_path()
        if not target.is_file():
            self._toast(f"Target exe not found: {target}", "error")
            return
        lnk_path = self._autostart_shortcut_path()
        try:
            lnk_path.parent.mkdir(parents=True, exist_ok=True)
            # Use COM via WScript.Shell (same approach as PowerShell).
            import pythoncom  # noqa: F401  # prerequisite for Dispatch on some setups
        except ImportError:
            # pywin32 not installed; fall back to PowerShell.
            self._repair_autostart_via_powershell(lnk_path, target)
            return
        try:
            from win32com.client import Dispatch  # type: ignore
            shell = Dispatch("WScript.Shell")
            sc = shell.CreateShortCut(str(lnk_path))
            sc.TargetPath = str(target)
            sc.Arguments = "--tray"
            sc.WorkingDirectory = str(target.parent)
            sc.WindowStyle = 7  # minimized
            sc.Description = "Claude Token Saver — system tray (auto-start)"
            sc.IconLocation = f"{target},0"
            sc.save()
            self._toast("Autostart shortcut repaired", "success")
        except Exception as e:
            self._log(f"COM shortcut creation failed: {e}; falling back to PowerShell")
            self._repair_autostart_via_powershell(lnk_path, target)
        self._refresh_autostart_status()

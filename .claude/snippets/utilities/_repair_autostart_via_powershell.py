# From: claude_backend/gui.py:3007
# PowerShell fallback for shortcut creation when pywin32 unavailable.

    def _repair_autostart_via_powershell(self, lnk_path: Path, target: Path) -> None:
        """PowerShell fallback for shortcut creation when pywin32 unavailable."""
        import subprocess
        ps_script = (
            f"$WshShell = New-Object -ComObject WScript.Shell;"
            f"$sc = $WshShell.CreateShortcut('{lnk_path}');"
            f"$sc.TargetPath = '{target}';"
            f"$sc.Arguments = '--tray';"
            f"$sc.WorkingDirectory = '{target.parent}';"
            f"$sc.WindowStyle = 7;"
            f"$sc.Description = 'Claude Token Saver tray (auto-start)';"
            f"$sc.IconLocation = '{target},0';"
            f"$sc.Save();"
        )
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script],
                capture_output=True, text=True, timeout=15,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )
            if result.returncode == 0 and lnk_path.is_file():
                self._toast("Autostart shortcut repaired", "success")
            else:
                self._toast(f"Repair failed: {result.stderr or 'unknown error'}", "error")
        except (OSError, subprocess.TimeoutExpired) as e:
            self._toast(f"Repair failed: {e}", "error")

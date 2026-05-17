# From: claude_backend/gui.py:3340
# Open the bundled extension folder in Explorer.

    def _open_extension_folder(self) -> None:
        """Open the bundled extension folder in Explorer."""
        # Try several locations: dev source tree, frozen exe sibling, etc.
        candidates = [
            Path(__file__).resolve().parent.parent / "extensions" / "claude_token_saver",
            Path.cwd() / "extensions" / "claude_token_saver",
        ]
        for cand in candidates:
            if cand.is_dir():
                try:
                    import subprocess
                    if sys.platform == "win32":
                        subprocess.Popen(
                            ["explorer", str(cand)],
                            creationflags=subprocess.CREATE_NO_WINDOW,
                        )
                    else:
                        subprocess.Popen(["xdg-open", str(cand)])
                    self._toast(f"Opened: {cand}", "info")
                    return
                except OSError as e:
                    self._toast(f"Open failed: {e}", "error")
                    return
        self._toast(
            "Extension folder not found. Look in source tree at "
            "extensions/claude_token_saver/",
            "warning",
        )

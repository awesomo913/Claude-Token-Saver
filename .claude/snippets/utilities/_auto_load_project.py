# From: claude_backend/gui.py:689
# Auto-load a remembered project on startup (silent — no toast).

    def _auto_load_project(self, path: Path) -> None:
        """Auto-load a remembered project on startup (silent — no toast)."""
        try:
            self._d_path.delete(0, "end")
            self._d_path.insert(0, str(path))
            self._project_path = path.resolve()
            self._config = load_config(project_path=self._project_path)
            self._mgr = ClaudeContextManager(self._config)
            self._session_mem.set_project(self._project_path)
            self._st_proj.configure(text=str(self._project_path))
            self._log(f"Auto-loaded last project: {self._project_path.name}")
            self._update_token_display()
            self._update_recent()
            # Defer scan so welcome dialog (if shown) doesn't compete for focus
            self.after(800, lambda: self._on_scan(start_auto_after=True))
        except Exception as e:
            logger.exception("Auto-load failed")
            self._log(f"Auto-load failed: {e}")

# From: claude_backend/gui.py:624

    def _on_load(self) -> None:
        ps = self._d_path.get().strip()
        if not ps: self._toast("Enter a project path first", "warning"); return
        p = Path(ps)
        if not p.is_dir(): self._toast("Not a valid directory", "error"); return
        self._project_path = p.resolve()
        self._config = load_config(project_path=self._project_path)
        self._mgr = ClaudeContextManager(self._config)
        self._session_mem.set_project(self._project_path)
        self._st_proj.configure(text=str(self._project_path))
        self._log(f"Loaded: {self._project_path.name}")
        self._toast(f"Project loaded: {self._project_path.name}", "success")
        self._update_token_display(); self._update_recent()
        # Persist for auto-load on next launch
        self._prefs.last_project_path = str(self._project_path)
        self._prefs.save()
        # Run initial scan FIRST, then start auto-scan timer after it completes
        self._on_scan(start_auto_after=True)

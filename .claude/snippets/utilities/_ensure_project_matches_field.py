# From: claude_backend/gui.py:643
# If the Project entry field path differs from `self._project_path`,

    def _ensure_project_matches_field(self) -> bool:
        """If the Project entry field path differs from `self._project_path`,
        auto-load the entry path so action buttons (Bootstrap/Prep/Scan/
        Clean) operate on the visible Project field instead of the
        previously-loaded one.

        Closes the UX trap where typing a new path into the field but
        forgetting to click LOAD made Bootstrap silently re-bootstrap
        the OLD project — the user reported "I bootstrapped but it
        didn't show up in the picker".

        Returns True if a valid project is loaded after the call,
        False if the field is empty/invalid (and a toast was shown).
        """
        ps = self._d_path.get().strip()
        if not ps:
            if not self._project_path:
                self._toast("Enter a project path first", "warning")
                return False
            return True  # blank field but a project is already loaded
        p = Path(ps)
        if not p.is_dir():
            self._toast(f"Not a valid directory: {ps}", "error")
            return False
        resolved = p.resolve()
        if (
            self._project_path is not None
            and resolved == self._project_path
        ):
            return True  # already loaded — no-op
        # Field differs from loaded — surface that we're switching.
        self._toast(
            f"Switching project to {resolved.name}", "info",
        )
        self._project_path = resolved
        self._config = load_config(project_path=self._project_path)
        self._mgr = ClaudeContextManager(self._config)
        self._session_mem.set_project(self._project_path)
        self._st_proj.configure(text=str(self._project_path))
        self._log(f"Loaded: {self._project_path.name} (auto)")
        self._prefs.last_project_path = str(self._project_path)
        self._prefs.save()
        self._update_token_display()
        self._update_recent()
        return True

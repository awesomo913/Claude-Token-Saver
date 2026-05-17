# From: claude_backend/gui.py:1880
# Check for file changes, only do a full rescan if something changed.

    def _auto_scan_tick(self) -> None:
        """Check for file changes, only do a full rescan if something changed."""
        from .scanners.project import scan_project_fast_mtimes

        if self._project_path and not self._busy:
            def do():
                new_mtimes = scan_project_fast_mtimes(self._project_path, self._config)
                # Compare against last known mtimes
                old_mtimes = getattr(self, '_last_mtimes', {})
                if new_mtimes != old_mtimes:
                    self._last_mtimes = new_mtimes
                    return self._mgr.analyze(self._project_path)  # full rescan
                return None  # no changes

            def done(a):
                if a is not None:
                    self._analysis = a
                    self._snippets = [b for b in a.blocks if b.docstring or b.kind != "file"]
                    self._update_stats(); self._load_memory()
                    self._rebuild_domain_tabs(); self._filter_snips()
                    self._rebuild_grab_buttons()
                    self._st_label.configure(text=f"Auto-scan: {len(a.files)} files (changed)")
                    self._log("Auto-scan: changes detected, refreshed")
                else:
                    self._st_label.configure(text="Auto-scan: no changes")
            self._run_async(do, done)
        self._auto_scan_id = self.after(self._auto_scan_interval, self._auto_scan_tick)

# From: NeoAutocoder/core_loop.py:174
# Organized auto-save per Fix 8.

    def _save_iteration(self, session: Session, iter_num: int, focus: str):
        """Organized auto-save per Fix 8."""
        project_slug = self._extract_project_slug(session.current_codebase) or "project"
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        
        iter_dir = self.output_dir / project_slug
        iter_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"iter_{iter_num:04d}_{focus.lower().replace(' ', '_')}_{timestamp}.py"
        path = iter_dir / filename
        path.write_text(session.current_codebase)
        
        # Also save metadata
        meta = {
            "iteration": iter_num,
            "focus": focus,
            "size_chars": len(session.current_codebase),
            "hash": session.last_hash,
            "timestamp": timestamp
        }
        (iter_dir / f"{filename}.meta.json").write_text(json.dumps(meta, indent=2))
        
        print(f"Saved: {path}")

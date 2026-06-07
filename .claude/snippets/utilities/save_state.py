# From: NeoAutocoder/session.py:45
# Persist session state.

    def save_state(self, base_dir: Path):
        """Persist session state."""
        state = {
            "session_id": self.session_id,
            "corner": self.corner,
            "iteration_count": self.iteration_count,
            "focus_history": self.focus_history,
            "last_hash": self.last_hash,
            "metrics": self.metrics,
            "timestamp": datetime.now().isoformat()
        }
        path = base_dir / f"session_{self.session_id}.json"
        path.write_text(json.dumps(state, indent=2))
        if self.codebase_path:
            self.codebase_path.write_text(self.current_codebase)

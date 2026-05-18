# From: claude_backend/tracker.py:213
# Get most recently added context items (newest first).

    def get_recently_used(self, limit: int = 15) -> list[dict]:
        """Get most recently added context items (newest first)."""
        history = self._data.get("context_history", [])
        return list(reversed(history[-limit:]))

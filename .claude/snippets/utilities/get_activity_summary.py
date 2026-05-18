# From: claude_backend/tracker.py:271
# Summary for dashboard display.

    def get_activity_summary(self) -> dict:
        """Summary for dashboard display."""
        history = self._data.get("context_history", [])
        copies = self._data.get("clipboard_copies", [])
        return {
            "total_items_added": len(history),
            "total_copies": len(copies),
            "unique_snippets": len({h["name"] for h in history}),
            "total_tokens_copied": sum(c.get("tokens", 0) for c in copies),
            "last_activity": history[-1]["ts"] if history else None,
        }

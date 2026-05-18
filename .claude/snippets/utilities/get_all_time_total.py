# From: claude_backend/tracker.py:83
# Total tokens AVOIDED (real savings, not just referenced).

    def get_all_time_total(self) -> int:
        """Total tokens AVOIDED (real savings, not just referenced)."""
        return sum(e.get("tokens_avoided", e.get("tokens", 0)) for e in self._events)

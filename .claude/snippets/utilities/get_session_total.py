# From: claude_backend/tracker.py:93
# Tokens avoided since a given ISO timestamp (current app session).

    def get_session_total(self, since_ts: str) -> int:
        """Tokens avoided since a given ISO timestamp (current app session)."""
        return sum(
            e.get("tokens_avoided", e.get("tokens", 0)) for e in self._events
            if e.get("ts", "") >= since_ts
        )

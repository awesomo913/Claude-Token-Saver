# From: gemini_coder/history.py:96
# Get recent history entries.

    def get_entries(self, limit: int = 50) -> List[HistoryEntry]:
        """Get recent history entries."""
        return list(reversed(self._entries))[:limit]

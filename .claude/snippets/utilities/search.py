# From: gemini_coder/history.py:105
# Search history for entries matching query.

    def search(self, query: str) -> List[HistoryEntry]:
        """Search history for entries matching query."""
        query_lower = query.lower()
        return [
            e for e in self._entries
            if query_lower in e.title.lower()
            or query_lower in e.prompt.lower()
        ]

# From: gemini_coder/history.py:89
# Add a new history entry.

    def add(self, entry: HistoryEntry) -> None:
        """Add a new history entry."""
        self._entries.append(entry)
        if len(self._entries) > self._max_entries:
            self._entries = self._entries[-self._max_entries:]
        self._save()

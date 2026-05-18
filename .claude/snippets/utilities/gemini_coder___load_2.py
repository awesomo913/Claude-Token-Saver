# From: gemini_coder/history.py:72
# Load history from disk.

    def _load(self) -> None:
        """Load history from disk."""
        if self._path.exists():
            try:
                data = json.loads(self._path.read_text(encoding="utf-8"))
                self._entries = [HistoryEntry.from_dict(e) for e in data]
            except Exception as e:
                logger.error("Failed to load history: %s", e)

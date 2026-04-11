# From: gemini_coder/history.py:46

class HistoryManager:
    """Manages task and conversation history."""

    def __init__(self, max_entries: int = 100) -> None:
        self._max_entries = max_entries
        self._entries: List[HistoryEntry] = []
        self._path = get_config_dir() / "history.json"
        self._load()

    def _load(self) -> None:
        """Load history from disk."""
        if self._path.exists():
            try:
                data = json.loads(self._path.read_text(encoding="utf-8"))
                self._entries = [HistoryEntry.from_dict(e) for e in data]
            except Exception as e:
                logger.error("Failed to load history: %s", e)

    def _save(self) -> None:
        """Save history to disk."""
        try:
            data = [e.to_dict() for e in self._entries[-self._max_entries:]]
            self._path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception as e:
            logger.error("Failed to save history: %s", e)

    def add(self, entry: HistoryEntry) -> None:
        """Add a new history entry."""
        self._entries.append(entry)
        if len(self._entries) > self._max_entries:
            self._entries = self._entries[-self._max_entries:]
        self._save()

    def get_entries(self, limit: int = 50) -> List[HistoryEntry]:
        """Get recent history entries."""
        return list(reversed(self._entries))[:limit]

    def clear(self) -> None:
        """Clear all history."""
        self._entries.clear()
        self._save()

    def search(self, query: str) -> List[HistoryEntry]:
        """Search history for entries matching query."""
        query_lower = query.lower()
        return [
            e for e in self._entries
            if query_lower in e.title.lower()
            or query_lower in e.prompt.lower()
        ]

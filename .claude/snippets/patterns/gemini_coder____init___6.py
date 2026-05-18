# From: gemini_coder/history.py:66

    def __init__(self, max_entries: int = 100) -> None:
        self._max_entries = max_entries
        self._entries: List[HistoryEntry] = []
        self._path = get_config_dir() / "history.json"
        self._load()

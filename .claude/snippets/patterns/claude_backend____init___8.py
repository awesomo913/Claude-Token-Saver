# From: claude_backend/tracker.py:125

    def __init__(self, project_path: Optional[Path] = None) -> None:
        self._project = project_path
        self._data: dict = {
            "context_history": [],    # items added to context
            "clipboard_copies": [],   # full context copies
            "connections": {},        # module -> [snippet names] for suggestions
        }
        if project_path:
            self._path = project_path / ".claude" / "session_context.json"
            self._load()
        else:
            self._path = None

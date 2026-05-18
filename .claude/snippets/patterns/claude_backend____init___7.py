# From: claude_backend/tracker.py:32

    def __init__(self) -> None:
        self.path = Path.home() / ".claude" / "token_savings.jsonl"
        self._events: list[dict] = []
        self._load()

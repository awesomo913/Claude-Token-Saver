# From: gemini_coder/history.py:15

class HistoryEntry:
    """A single entry in the history."""

    def __init__(
        self,
        entry_type: str = "task",
        title: str = "",
        prompt: str = "",
        response: str = "",
        model: str = "",
        elapsed_seconds: float = 0.0,
        status: str = "completed",
        timestamp: Optional[str] = None,
    ):
        self.entry_type = entry_type
        self.title = title
        self.prompt = prompt
        self.response = response
        self.model = model
        self.elapsed_seconds = elapsed_seconds
        self.status = status
        self.timestamp = timestamp or datetime.now().isoformat()

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "HistoryEntry":
        return cls(**data)

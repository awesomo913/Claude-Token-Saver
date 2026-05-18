# From: gemini_coder/history.py:15
# A single entry in the history.

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
        # HistoryEntry is a plain class, not a @dataclass, so asdict() fails.
        # Serialize the fields the __init__ accepts.
        return {
            "entry_type": self.entry_type,
            "title": self.title,
            "prompt": self.prompt,
            "response": self.response,
            "model": self.model,
            "elapsed_seconds": self.elapsed_seconds,
            "status": self.status,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "HistoryEntry":
        # Drop unknown keys from older schemas (e.g. legacy 'id' field) so
        # loading doesn't crash with TypeError.
        known = {
            "entry_type", "title", "prompt", "response", "model",
            "elapsed_seconds", "status", "timestamp",
        }
        return cls(**{k: v for k, v in data.items() if k in known})

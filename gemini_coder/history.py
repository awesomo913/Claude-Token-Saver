"""History management for Gemini Coder."""

import json
import logging
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .platform_utils import get_config_dir

logger = logging.getLogger(__name__)


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

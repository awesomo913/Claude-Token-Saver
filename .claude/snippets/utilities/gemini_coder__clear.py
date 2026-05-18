# From: gemini_coder/history.py:100
# Clear all history.

    def clear(self) -> None:
        """Clear all history."""
        self._entries.clear()
        self._save()

# From: gemini_coder/history.py:81
# Save history to disk.

    def _save(self) -> None:
        """Save history to disk."""
        try:
            data = [e.to_dict() for e in self._entries[-self._max_entries:]]
            self._path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception as e:
            logger.error("Failed to save history: %s", e)

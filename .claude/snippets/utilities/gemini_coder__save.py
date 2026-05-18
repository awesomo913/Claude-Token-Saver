# From: gemini_coder/config.py:45
# Save configuration to disk.

    def save(self) -> None:
        """Save configuration to disk."""
        data = asdict(self.config)
        self._path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

# From: claude_backend/manifest.py:54
# Write manifest to disk.

    def save(self) -> None:
        """Write manifest to disk."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            lines = [
                json.dumps(asdict(entry), ensure_ascii=False)
                for entry in self._entries.values()
            ]
            self.path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        except OSError as e:
            logger.warning("Failed to save manifest: %s", e)

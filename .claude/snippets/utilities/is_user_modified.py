# From: claude_backend/manifest.py:84
# Check if a generated file was modified by the user after generation.

    def is_user_modified(self, path: str, actual_path: Path) -> bool:
        """Check if a generated file was modified by the user after generation."""
        entry = self._entries.get(path)
        if entry is None:
            return False
        if not actual_path.is_file():
            return False
        actual_hash = _hash_str(actual_path.read_text(encoding="utf-8", errors="replace"))
        return actual_hash != entry.sha256

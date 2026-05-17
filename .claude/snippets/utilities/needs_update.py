# From: claude_backend/manifest.py:66
# Check if a generated file needs updating.

    def needs_update(self, path: str, content: str, source_hash: str = "") -> bool:
        """Check if a generated file needs updating.

        Returns True if:
        - File not in manifest (new)
        - Source hash changed (source modified)
        - Generated content hash differs from manifest (we'd produce different output)
        """
        content_hash = _hash_str(content)
        entry = self._entries.get(path)
        if entry is None:
            return True
        if source_hash and entry.source_hash and source_hash != entry.source_hash:
            return True
        if entry.sha256 != content_hash:
            return True
        return False

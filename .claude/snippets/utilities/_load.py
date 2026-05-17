# From: claude_backend/manifest.py:35
# Load existing manifest from disk.

    def _load(self) -> None:
        """Load existing manifest from disk."""
        if not self.path.is_file():
            return
        try:
            for line in self.path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)
                entry = ManifestEntry(**{
                    k: v for k, v in data.items()
                    if k in ManifestEntry.__dataclass_fields__
                })
                self._entries[entry.path] = entry
            logger.debug("Loaded %d manifest entries from %s", len(self._entries), self.path)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Failed to load manifest %s: %s", self.path, e)

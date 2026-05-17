# From: claude_backend/manifest.py:94
# Record a generated file in the manifest.

    def record(
        self,
        path: str,
        content: str,
        generator: str = "",
        source_hash: str = "",
    ) -> None:
        """Record a generated file in the manifest."""
        self._entries[path] = ManifestEntry(
            path=path,
            sha256=_hash_str(content),
            source_hash=source_hash,
            generator=generator,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

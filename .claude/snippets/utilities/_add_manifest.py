# From: claude_backend/storage.py:75
# Append an entry to the manifest.

    def _add_manifest(self, path: str, **extra: object) -> None:
        """Append an entry to the manifest."""
        entry = {"path": path, "ts": _now_iso(), **extra}
        try:
            with self.manifest_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except OSError as e:
            logger.warning("Failed to write manifest: %s", e)

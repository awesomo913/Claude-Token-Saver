# From: claude_backend/storage.py:24
# Write content to a file under the project directory.

    def write_file(self, rel_path: str, content: str, source: str = "") -> bool:
        """Write content to a file under the project directory.

        Returns True if file was written, False if it already existed unchanged.
        """
        safe_parts = _normalize_path(rel_path)
        if not safe_parts:
            logger.warning("Skipping empty path: %r", rel_path)
            return False

        dest = self.project_dir
        for part in safe_parts[:-1]:
            dest = dest / part
        dest.mkdir(parents=True, exist_ok=True)
        dest = dest / safe_parts[-1]

        if dest.is_file():
            existing = dest.read_text(encoding="utf-8", errors="replace")
            if existing == content:
                self._log_event("skipped_unchanged", str(dest), source=source)
                return False

        dest.write_text(content, encoding="utf-8")
        self._log_event("file_written", str(dest), length=len(content), source=source)
        self._add_manifest(str(dest), source=source, length=len(content))
        return True

# From: claude_backend/storage.py:55
# List all files in the project directory (relative paths).

    def list_files(self) -> list[str]:
        """List all files in the project directory (relative paths)."""
        result = []
        for p in sorted(self.project_dir.rglob("*")):
            if p.is_file() and p.name not in ("CLAUDE_LOG.jsonl", "CLAUDE_MANIFEST.jsonl"):
                try:
                    result.append(str(p.relative_to(self.project_dir)))
                except ValueError:
                    result.append(str(p))
        return result

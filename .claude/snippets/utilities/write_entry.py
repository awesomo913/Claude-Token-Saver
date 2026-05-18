# From: claude_backend/storage.py:51
# Write a FileEntry to the project directory.

    def write_entry(self, entry: FileEntry) -> bool:
        """Write a FileEntry to the project directory."""
        return self.write_file(entry.path, entry.content, source=entry.source)

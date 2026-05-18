# From: claude_backend/scanners/project.py:208
# Find likely entry point files.

def find_entry_points(entries: list[FileEntry]) -> list[str]:
    """Find likely entry point files."""
    markers = ["if __name__", "def main(", "app.mainloop(", "app.run("]
    result = []
    for e in entries:
        if any(m in e.content for m in markers):
            result.append(e.path)
    return result

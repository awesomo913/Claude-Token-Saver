# From: claude_backend/analyzers/structure_mapper.py:82
# Check if source contains common entry point patterns.

def _is_entry_point(source: str) -> bool:
    """Check if source contains common entry point patterns."""
    markers = ['if __name__ == "__main__"', "if __name__ == '__main__'",
               "def main(", "app.mainloop(", "app.run("]
    return any(m in source for m in markers)

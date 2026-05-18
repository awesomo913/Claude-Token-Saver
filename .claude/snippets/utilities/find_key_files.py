# From: claude_backend/scanners/project.py:218
# Find important project files that exist at the root.

def find_key_files(root: Path) -> list[str]:
    """Find important project files that exist at the root."""
    names = [
        "README.md", "README.rst", "README.txt",
        "CLAUDE.md", "setup.py", "setup.cfg",
        "pyproject.toml", "package.json", "Cargo.toml",
        "requirements.txt", "Makefile", "Dockerfile",
        ".gitignore",
    ]
    found = []
    for name in names:
        if (root / name).is_file():
            found.append(name)
    return found

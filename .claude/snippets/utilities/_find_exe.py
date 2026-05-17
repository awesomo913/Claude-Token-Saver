# From: claude_backend/session_launcher.py:45
# Locate ClaudeTokenSaver.exe on disk. Prefer Desktop deploy.

def _find_exe() -> Path | None:
    """Locate ClaudeTokenSaver.exe on disk. Prefer Desktop deploy."""
    if _DEFAULT_EXE_PATH.is_file():
        return _DEFAULT_EXE_PATH
    # Could extend with PATH lookup or registry in future; for now, just Desktop.
    return None

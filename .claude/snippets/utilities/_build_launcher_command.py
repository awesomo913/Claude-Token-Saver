# From: claude_backend/auto_inject.py:86
# Hook command that runs session_launcher (reads prefs, decides what to do).

def _build_launcher_command() -> str:
    """Hook command that runs session_launcher (reads prefs, decides what to do)."""
    python_exe = _find_pythonw()
    return f'"{python_exe}" -m claude_backend.session_launcher || true'

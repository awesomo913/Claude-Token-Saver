# From: claude_backend/auto_inject.py:77
# Hook command that runs prep silently on session start.

def _build_prep_command() -> str:
    """Hook command that runs prep silently on session start."""
    python_exe = sys.executable.replace("\\", "/")
    return (
        f'"{python_exe}" -m claude_backend prep '
        f'"${{CLAUDE_PROJECT_DIR:-.}}" --quiet || true'
    )

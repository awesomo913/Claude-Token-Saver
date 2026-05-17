# From: claude_backend/auto_inject.py:67
# Return path to pythonw.exe (Windows, no console) or fallback to python.

def _find_pythonw() -> str:
    """Return path to pythonw.exe (Windows, no console) or fallback to python."""
    exe = Path(sys.executable)
    if sys.platform == "win32" and exe.name.lower() == "python.exe":
        candidate = exe.with_name("pythonw.exe")
        if candidate.is_file():
            return str(candidate).replace("\\", "/")
    return sys.executable.replace("\\", "/")

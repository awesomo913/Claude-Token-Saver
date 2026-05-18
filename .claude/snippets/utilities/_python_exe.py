# From: claude_backend/tray.py:95
# Find pythonw.exe (no console) on Windows; fallback to sys.executable.

def _python_exe() -> str:
    """Find pythonw.exe (no console) on Windows; fallback to sys.executable."""
    exe = Path(sys.executable)
    if exe.name.lower() == "python.exe":
        candidate = exe.with_name("pythonw.exe")
        if candidate.is_file():
            return str(candidate)
    return sys.executable

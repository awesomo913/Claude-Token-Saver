# From: claude_backend/http_server.py:453
# If GUI not running, spawn it. Returns True if it should appear soon.

def ensure_gui_running() -> bool:
    """If GUI not running, spawn it. Returns True if it should appear soon."""
    try:
        from .single_instance import is_locked
        if is_locked("ClaudeTokenSaverGUI"):
            return True
    except Exception as e:
        logger.debug("is_locked check failed: %s", e)

    # Spawn GUI subprocess. Reuse session_launcher's spawn helper for
    # consistency in detached-process flags.
    try:
        from .session_launcher import _spawn_detached, _find_exe
        exe = _find_exe()
        if exe is not None:
            return _spawn_detached([str(exe)])
        # Fallback to python -m
        py = sys.executable
        if sys.platform == "win32":
            cand = Path(py).with_name("pythonw.exe")
            if cand.is_file():
                py = str(cand)
        return _spawn_detached([py, "-m", "claude_backend.gui"])
    except Exception as e:
        logger.warning("Failed to spawn GUI: %s", e)
        return False

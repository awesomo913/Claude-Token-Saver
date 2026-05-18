# From: claude_backend/tray.py:105
# Spawn the overlay as a detached subprocess.

def _spawn_overlay_subprocess() -> None:
    """Spawn the overlay as a detached subprocess.

    Uses the deployed exe when available (frozen mode); falls back to
    `python -m claude_backend.overlay` for dev runs. Single-instance
    lock inside the overlay module guarantees no duplicate windows.
    """
    creationflags = 0
    if sys.platform == "win32":
        creationflags = subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS

    exe_path = Path.home() / "Desktop" / "My Apps" / "ClaudeTokenSaver" / "ClaudeTokenSaver.exe"
    if exe_path.is_file():
        # Pass --overlay flag so the launcher routes to overlay mode.
        args = [str(exe_path), "--overlay"]
    else:
        args = [_python_exe(), "-m", "claude_backend.overlay"]

    subprocess.Popen(args, creationflags=creationflags, close_fds=True)

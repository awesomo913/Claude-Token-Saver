# From: claude_backend/tray.py:126
# Open Token Saver GUI in detached subprocess.

def _launch_gui(icon: Optional["pystray.Icon"] = None) -> None:
    """Open Token Saver GUI in detached subprocess."""
    creationflags = 0
    if sys.platform == "win32":
        creationflags = subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS

    try:
        subprocess.Popen(
            [_python_exe(), "-m", "claude_backend.gui"],
            creationflags=creationflags,
            close_fds=True,
        )
    except OSError as e:
        logger.error("Failed to launch GUI: %s", e)

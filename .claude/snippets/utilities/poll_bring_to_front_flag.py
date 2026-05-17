# From: claude_backend/single_instance.py:171
# Called from the running instance's Tk after-loop (every ~1s).

def poll_bring_to_front_flag(
    name: str, callback: Callable[[], None],
) -> bool:
    """Called from the running instance's Tk after-loop (every ~1s).
    If the flag file exists, delete it and invoke ``callback`` so the
    GUI can raise its own window. Returns True when a raise fired."""
    p = _flag_path(name)
    if not p.is_file():
        return False
    try:
        p.unlink()
    except OSError:
        pass
    try:
        callback()
    except Exception:  # noqa: BLE001
        logger.exception("bring-to-front callback failed")
    return True

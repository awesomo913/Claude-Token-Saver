# From: claude_backend/session_launcher.py:53
# Spawn a detached subprocess so the hook can return immediately.

def _spawn_detached(args: list[str]) -> bool:
    """Spawn a detached subprocess so the hook can return immediately.

    Returns True on success. Errors are logged, never raised — we must
    not block Claude Code session start.
    """
    try:
        kwargs: dict = {"close_fds": True}
        if sys.platform == "win32":
            kwargs["creationflags"] = (
                subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS
            )
        else:
            # POSIX: detach via setsid so spawned process survives parent exit.
            kwargs["start_new_session"] = True
        subprocess.Popen(args, **kwargs)
        return True
    except OSError as e:
        logger.warning("session_launcher: spawn failed: %s", e)
        return False

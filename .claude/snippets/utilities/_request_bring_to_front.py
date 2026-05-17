# From: claude_backend/single_instance.py:159
# Write a tiny raise-flag file. Running instance polls for it

def _request_bring_to_front(name: str) -> None:
    """Write a tiny raise-flag file. Running instance polls for it
    via ``poll_bring_to_front_flag`` and raises its window. Simpler
    than WM_COPYDATA because CTk window class names aren't stable."""
    try:
        p = _flag_path(name)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(str(os.getpid()), encoding="utf-8")
    except OSError as e:
        logger.debug("could not write raise flag: %s", e)

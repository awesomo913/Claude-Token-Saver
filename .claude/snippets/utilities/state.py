# From: claude_backend/diagnostics_logger.py:139
# Log a STATE transition (e.g. 'init->ready', 'ready->shutdown').

def state(transition: str) -> None:
    """Log a STATE transition (e.g. 'init->ready', 'ready->shutdown')."""
    logging.getLogger("state").info("STATE %s", transition)

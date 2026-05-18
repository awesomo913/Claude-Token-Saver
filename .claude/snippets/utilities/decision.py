# From: claude_backend/diagnostics_logger.py:129
# Log a non-trivial branch (e.g. 'cleanup=skipped reason=no-stale-flag').

def decision(detail: str) -> None:
    """Log a non-trivial branch (e.g. 'cleanup=skipped reason=no-stale-flag')."""
    logging.getLogger("decision").info("DECISION %s", detail)

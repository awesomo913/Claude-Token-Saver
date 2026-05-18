# From: claude_backend/diagnostics_logger.py:149
# Log a timed operation (e.g. perf('tk_root_init', 0.42)).

def perf(label: str, seconds: float) -> None:
    """Log a timed operation (e.g. perf('tk_root_init', 0.42))."""
    logging.getLogger("perf").info("PERF %s=%.3fs", label, seconds)

# From: gemini_coder/safe_exec.py:10
# Safely call a function, returning default on exception.

def safe_call(func: Callable, *args, default: Any = None, **kwargs) -> Any:
    """Safely call a function, returning default on exception."""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.error("safe_call failed: %s", e)
        logger.debug("Traceback: %s", traceback.format_exc())
        return default

# From: gemini_coder/safe_exec.py:20
# Safely execute code, returning the result or None on error.

def safe_exec(code: str, globals_dict: dict = None, locals_dict: dict = None) -> Any:
    """Safely execute code, returning the result or None on error."""
    if globals_dict is None:
        globals_dict = {}
    if locals_dict is None:
        locals_dict = {}
    
    try:
        return exec(code, globals_dict, locals_dict)
    except Exception as e:
        logger.error("safe_exec failed: %s", e)
        logger.debug("Traceback: %s", traceback.format_exc())
        return None

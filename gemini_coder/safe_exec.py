"""Safe execution utilities."""

import logging
import traceback
from typing import Any, Callable

logger = logging.getLogger(__name__)


def safe_call(func: Callable, *args, default: Any = None, **kwargs) -> Any:
    """Safely call a function, returning default on exception."""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.error("safe_call failed: %s", e)
        logger.debug("Traceback: %s", traceback.format_exc())
        return default


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


def extract_code_blocks(text: str) -> list[str]:
    """Extract code blocks from markdown text."""
    import re
    pattern = r'```(?:\w+)?\n(.*?)```'
    matches = re.findall(pattern, text, re.DOTALL)
    return [block.strip() for block in matches if block.strip()]


def clean_code(code: str) -> str:
    """Clean extracted code by removing common AI artifacts."""
    code = code.strip()
    
    if code.startswith("```"):
        lines = code.split('\n')
        code = '\n'.join(lines[1:] if lines[0].startswith("```") else lines)
    
    if code.endswith("```"):
        code = code[:-3].strip()
    
    return code

# From: claude_backend/generators/snippet_library.py:190
# Check if a function looks like a reusable pattern.

def _is_pattern(block: CodeBlock) -> bool:
    """Check if a function looks like a reusable pattern."""
    pattern_indicators = [
        "setup", "configure", "init", "create", "build",
        "parse", "load", "save", "validate", "format",
        "connect", "retry", "wrap", "decorate", "register",
    ]
    name_lower = block.name.lower()
    return any(ind in name_lower for ind in pattern_indicators)

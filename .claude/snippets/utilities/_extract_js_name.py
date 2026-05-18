# From: claude_backend/analyzers/code_extractor.py:204
# Extract the name from a JS declaration.

def _extract_js_name(block: str) -> str:
    """Extract the name from a JS declaration."""
    m = _JS_NAME_RE.search(block[:200])
    return m.group(1) if m else "anonymous"

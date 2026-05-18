# From: claude_backend/search.py:376
# Tokenize a symbol: underscores, whitespace, AND camelCase boundaries.

def _split_name(name: str) -> list[str]:
    """Tokenize a symbol: underscores, whitespace, AND camelCase boundaries.

    `TokenTracker` was previously indexed as the single token "tokentracker"
    because lowercasing happened before splitting. Queries like "token tracker"
    never matched. Splitting on camelCase first preserves the word boundaries
    that callers actually type.

    Examples:
        "TokenTracker"   -> ["token", "tracker"]
        "HTTPServer"     -> ["http", "server"]
        "send_message"   -> ["send", "message"]
        "_show_picker"   -> ["show", "picker"]
        "run_improve_pipeline" -> ["run", "improve", "pipeline"]
    """
    parts = re.split(r"[_\s]+", name)
    out: list[str] = []
    for p in parts:
        if not p:
            continue
        # Camel boundaries: HTTPServer -> HTTP, Server  // tokenTracker -> token, Tracker
        # Pattern grabs: acronym-runs, lower/digit runs, single uppercase, digits.
        camel = re.findall(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z0-9]+|[A-Z]+|\d+", p)
        out.extend((c.lower() for c in camel) if camel else [p.lower()])
    return [w for w in out if w]

# From: claude_backend/generators/memory_files.py:58
# Generate a 'hot functions' memory file from session_context.json.

def _gen_hot_functions(analysis: ProjectAnalysis) -> str:
    """Generate a 'hot functions' memory file from session_context.json.

    Lists the functions the user has most recently and most frequently
    added to their context. Claude auto-loads this, so their most-used
    code is already in context without manual intervention.
    """
    import json
    from collections import Counter

    session_path = analysis.root / ".claude" / "session_context.json"
    if not session_path.is_file():
        return ""

    try:
        data = json.loads(session_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return ""

    history = data.get("context_history", [])
    if not history:
        return ""

    # Count usage per function name
    usage = Counter()
    sources = {}
    for entry in history:
        name = entry.get("name", "")
        src = entry.get("source", "") or entry.get("file_path", "")
        if name:
            usage[name] += 1
            if name not in sources:
                sources[name] = src

    if not usage:
        return ""

    # Top 15 most-used functions
    top = usage.most_common(15)

    lines = [
        "---",
        f"name: {analysis.name} Hot Functions",
        f"description: Most-referenced code in recent sessions",
        "type: reference",
        "---",
        "",
        f"# Frequently Referenced Code ({analysis.name})",
        "",
        "These are the functions/classes you reference most often when working",
        "on this project. Keep them in mind for upcoming work.",
        "",
        "| Function/Class | Source File | Times Used |",
        "|---|---|---|",
    ]
    for name, count in top:
        src = sources.get(name, "?")
        lines.append(f"| `{name}` | `{src}` | {count} |")

    lines.append("")
    return "\n".join(lines)

# From: claude_backend/auto_inject.py:195
# Remove all inner hooks matching (hook_id, legacy_substr).

def _filter_session_hooks(
    session_hooks: list,
    hook_id: str,
    legacy_substr: str | None,
) -> tuple[list, int]:
    """Remove all inner hooks matching (hook_id, legacy_substr).

    Returns (filtered_session_hooks, removed_count). Empty entries
    (entry with no remaining inner hooks) are dropped entirely.
    """
    out: list = []
    removed = 0
    for entry in session_hooks:
        if not isinstance(entry, dict):
            out.append(entry)
            continue
        inner = entry.get("hooks", [])
        if not isinstance(inner, list):
            out.append(entry)
            continue
        kept = [h for h in inner if not _hook_matches(h, hook_id, legacy_substr)]
        if len(kept) == len(inner):
            out.append(entry)
            continue
        removed += len(inner) - len(kept)
        if kept:
            entry["hooks"] = kept
            out.append(entry)
        # else drop the whole entry
    return out, removed

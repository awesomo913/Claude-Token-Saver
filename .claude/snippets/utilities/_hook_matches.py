# From: claude_backend/auto_inject.py:177
# True if inner hook entry should be considered ours.

def _hook_matches(h: dict, hook_id: str, legacy_substr: str | None) -> bool:
    """True if inner hook entry should be considered ours.

    Strict: exact "# id" field equality. Falls back to command substring
    ONLY when "# id" is missing/empty (legacy hooks installed before this
    field existed). Once a hook has any "# id", that field is the sole
    source of truth — preventing accidental match of unrelated hooks.
    """
    if not isinstance(h, dict):
        return False
    annotated_id = str(h.get("# id", "")).strip()
    if annotated_id:
        return annotated_id == hook_id
    if legacy_substr:
        return legacy_substr in str(h.get("command", ""))
    return False

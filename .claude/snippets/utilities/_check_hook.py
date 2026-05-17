# From: claude_backend/auto_inject.py:227
# Generic status check for any hook id under any Claude Code hook event.

def _check_hook(
    hook_id: str, legacy_substr: str | None, event: str = "SessionStart",
) -> dict:
    """Generic status check for any hook id under any Claude Code hook event."""
    status = {
        "installed": False,
        "settings_valid": False,
        "settings_exists": SETTINGS_PATH.is_file(),
        "error": "",
    }
    data, err = _load_settings()
    if data is None:
        status["error"] = err
        return status
    status["settings_valid"] = True
    hooks = data.get("hooks", {}) if isinstance(data, dict) else {}
    event_hooks = hooks.get(event, []) if isinstance(hooks, dict) else []
    if not isinstance(event_hooks, list):
        return status
    for entry in event_hooks:
        if not isinstance(entry, dict):
            continue
        for h in entry.get("hooks", []) or []:
            if _hook_matches(h, hook_id, legacy_substr):
                status["installed"] = True
                return status
    return status

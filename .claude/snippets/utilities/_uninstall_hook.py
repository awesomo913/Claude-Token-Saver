# From: claude_backend/auto_inject.py:303
# Remove a hook by id from any Claude Code hook event.

def _uninstall_hook(
    hook_id: str, legacy_substr: str | None, event: str = "SessionStart",
) -> tuple[bool, str]:
    """Remove a hook by id from any Claude Code hook event."""
    data, err = _load_settings()
    if data is None:
        return False, err

    if not isinstance(data, dict):
        return False, "settings.json must be a JSON object"

    hooks = data.get("hooks", {})
    if not isinstance(hooks, dict):
        return False, "Hook not found (nothing to uninstall)"
    event_hooks = hooks.get(event, [])
    if not isinstance(event_hooks, list):
        return False, "Hook not found (nothing to uninstall)"

    filtered, removed = _filter_session_hooks(
        event_hooks, hook_id, legacy_substr,
    )

    if removed == 0:
        return False, "Hook not found (nothing to uninstall)"

    if filtered:
        hooks[event] = filtered
    else:
        hooks.pop(event, None)
        if not hooks:
            data.pop("hooks", None)

    ok, msg = _save_settings(data)
    if not ok:
        return False, msg
    return True, f"Uninstalled {removed} entr{'y' if removed == 1 else 'ies'}. {msg}"

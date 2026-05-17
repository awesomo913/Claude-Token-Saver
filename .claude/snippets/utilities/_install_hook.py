# From: claude_backend/auto_inject.py:256
# Install a hook under any Claude Code hook event; dedupes existing first.

def _install_hook(
    hook_id: str,
    description: str,
    command: str,
    legacy_substr: str | None,
    event: str = "SessionStart",
) -> tuple[bool, str]:
    """Install a hook under any Claude Code hook event; dedupes existing first."""
    data, err = _load_settings()
    if data is None:
        return False, err

    if not isinstance(data, dict):
        return False, "settings.json must be a JSON object"

    hooks = data.setdefault("hooks", {})
    event_hooks = hooks.setdefault(event, [])
    if not isinstance(event_hooks, list):
        return False, f"settings.json hooks.{event} must be a JSON array"

    # Dedupe: remove any existing entries matching this hook id (incl. legacy).
    event_hooks, removed = _filter_session_hooks(
        event_hooks, hook_id, legacy_substr,
    )

    # Append fresh entry.
    new_entry = {
        "matcher": "",
        "hooks": [
            {
                "type": "command",
                "command": command,
                "# id": hook_id,
                "# description": description,
            }
        ],
    }
    event_hooks.append(new_entry)
    hooks[event] = event_hooks

    ok, msg = _save_settings(data)
    if not ok:
        return False, msg
    suffix = f" (replaced {removed} stale entr{'y' if removed == 1 else 'ies'})" if removed else ""
    return True, f"Installed!{suffix} {msg}"

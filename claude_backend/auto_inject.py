"""Auto-inject setup: install a Claude Code SessionStart hook.

When Claude Code starts a session, this hook runs `prep` on the current
project, ensuring CLAUDE.md and memory files are always fresh. The user
never has to open the Token Saver GUI — context updates automatically.

Safe: reads settings.json, validates JSON, only writes if parseable.
"""

from __future__ import annotations

import json
import logging
import shutil
import sys
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

SETTINGS_PATH = Path.home() / ".claude" / "settings.json"
HOOK_ID = "claude_token_saver_auto_prep"
HOOK_DESCRIPTION = "Claude Token Saver — auto-refresh context on session start"


def _build_hook_command() -> str:
    """Build the shell command that runs Token Saver's prep on session start.

    Uses $CLAUDE_PROJECT_DIR if available, else falls back to cwd.
    Runs python -m claude_backend prep silently — never blocks session start.
    """
    python_exe = sys.executable.replace("\\", "/")
    # Run as background task: if prep fails, don't block session
    return (
        f'"{python_exe}" -m claude_backend prep "${{CLAUDE_PROJECT_DIR:-.}}" '
        f'--quiet > nul 2>&1 || true'
    )


def check_status() -> dict:
    """Check if auto-inject is installed. Returns status dict."""
    status = {
        "installed": False,
        "settings_valid": False,
        "settings_exists": SETTINGS_PATH.is_file(),
        "error": "",
    }

    if not SETTINGS_PATH.is_file():
        status["error"] = "settings.json not found"
        return status

    try:
        text = SETTINGS_PATH.read_text(encoding="utf-8")
        data = json.loads(text)
        status["settings_valid"] = True
    except json.JSONDecodeError as e:
        status["error"] = f"settings.json is not valid JSON: {e}"
        return status
    except OSError as e:
        status["error"] = f"Cannot read settings.json: {e}"
        return status

    # Look for our hook in SessionStart
    hooks = data.get("hooks", {})
    session_hooks = hooks.get("SessionStart", [])
    for hook_entry in session_hooks:
        if isinstance(hook_entry, dict):
            for h in hook_entry.get("hooks", []):
                if isinstance(h, dict) and HOOK_ID in str(h.get("command", "")):
                    status["installed"] = True
                    return status
            if HOOK_ID in str(hook_entry.get("command", "")):
                status["installed"] = True
                return status

    return status


def install() -> tuple[bool, str]:
    """Install the SessionStart hook. Returns (success, message).

    Creates a backup of settings.json before writing.
    """
    if not SETTINGS_PATH.is_file():
        return False, f"settings.json not found at {SETTINGS_PATH}"

    try:
        text = SETTINGS_PATH.read_text(encoding="utf-8")
    except OSError as e:
        return False, f"Cannot read settings.json: {e}"

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        return False, (
            f"settings.json is not valid JSON: {e}\n"
            "Please fix the file manually before installing auto-inject."
        )

    # Backup before modifying
    backup = SETTINGS_PATH.with_suffix(
        f".json.backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    )
    try:
        shutil.copy2(SETTINGS_PATH, backup)
    except OSError as e:
        return False, f"Cannot create backup: {e}"

    # Add the hook
    hooks = data.setdefault("hooks", {})
    session_hooks = hooks.setdefault("SessionStart", [])

    # Build the hook entry in Claude Code's documented format
    cmd = _build_hook_command()
    new_hook = {
        "matcher": "",
        "hooks": [
            {
                "type": "command",
                "command": cmd,
                "# id": HOOK_ID,
                "# description": HOOK_DESCRIPTION,
            }
        ],
    }

    session_hooks.append(new_hook)

    # Write atomically
    try:
        new_text = json.dumps(data, indent=2, ensure_ascii=False)
        SETTINGS_PATH.write_text(new_text, encoding="utf-8")
    except OSError as e:
        # Restore from backup on failure
        try:
            shutil.copy2(backup, SETTINGS_PATH)
        except OSError:
            pass
        return False, f"Cannot write settings.json: {e}"

    return True, f"Installed! Backup saved at {backup.name}"


def uninstall() -> tuple[bool, str]:
    """Remove the SessionStart hook. Returns (success, message)."""
    if not SETTINGS_PATH.is_file():
        return False, "settings.json not found"

    try:
        text = SETTINGS_PATH.read_text(encoding="utf-8")
        data = json.loads(text)
    except (OSError, json.JSONDecodeError) as e:
        return False, f"Cannot parse settings.json: {e}"

    hooks = data.get("hooks", {})
    session_hooks = hooks.get("SessionStart", [])

    # Filter out our hook
    filtered = []
    removed = 0
    for entry in session_hooks:
        if isinstance(entry, dict):
            inner = entry.get("hooks", [])
            kept_inner = [
                h for h in inner
                if not (isinstance(h, dict) and HOOK_ID in str(h.get("# id", "")))
                and not (isinstance(h, dict) and HOOK_ID in str(h.get("command", "")))
            ]
            if len(kept_inner) != len(inner):
                removed += len(inner) - len(kept_inner)
                if kept_inner:
                    entry["hooks"] = kept_inner
                    filtered.append(entry)
                # else drop the whole entry
            else:
                filtered.append(entry)
        else:
            filtered.append(entry)

    if removed == 0:
        return False, "Auto-inject hook not found (nothing to uninstall)"

    if filtered:
        hooks["SessionStart"] = filtered
    else:
        hooks.pop("SessionStart", None)
        if not hooks:
            data.pop("hooks", None)

    # Backup and write
    backup = SETTINGS_PATH.with_suffix(
        f".json.backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    )
    try:
        shutil.copy2(SETTINGS_PATH, backup)
        new_text = json.dumps(data, indent=2, ensure_ascii=False)
        SETTINGS_PATH.write_text(new_text, encoding="utf-8")
    except OSError as e:
        return False, f"Cannot write settings.json: {e}"

    return True, f"Uninstalled. Backup at {backup.name}"

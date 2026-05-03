"""Auto-inject setup: install Claude Code SessionStart hooks.

Two distinct hooks managed by this module:

1. PREP hook (HOOK_ID): runs `prep` on session start to refresh CLAUDE.md
   and memory files. Always silent. The original Auto-Inject feature.

2. LAUNCH hook (HOOK_ID_LAUNCH): runs `session_launcher` on session start
   to optionally auto-open the Token Saver GUI/tray. Behavior controlled
   by user prefs at runtime — hook itself is a thin wrapper.

Safety:
- Reads settings.json, validates JSON, only writes if parseable.
- Atomic write (temp file + os.replace) prevents partial-write corruption.
- Timestamped backups; retention policy keeps only the newest 3.
- Uninstall matches ONLY by exact "# id" field (with legacy substring
  fallback for hooks installed before "# id" annotations existed).
- Install deduplicates: if an old/duplicate prep hook exists (e.g. the
  pre-`# id` version with a stale `> nul` redirect), it is removed
  before the fresh hook is appended. Prevents the prep-runs-twice
  failure when re-installing.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# ── Paths and IDs ───────────────────────────────────────────────────

SETTINGS_PATH = Path.home() / ".claude" / "settings.json"

# Prep hook (refreshes CLAUDE.md + memory files).
HOOK_ID = "claude_token_saver_auto_prep"
HOOK_DESCRIPTION = "Claude Token Saver — auto-refresh context on session start"

# Launcher hook (auto-opens GUI/tray if enabled in prefs).
HOOK_ID_LAUNCH = "claude_token_saver_session_launch"
HOOK_DESC_LAUNCH = (
    "Claude Token Saver — auto-launch GUI on session start (gated by user pref)"
)

# Substring patterns used as legacy fallback when "# id" field is missing.
# Kept tight so unrelated user hooks aren't accidentally matched.
_PREP_LEGACY_SUBSTR = "-m claude_backend prep"
_LAUNCH_LEGACY_SUBSTR = "claude_backend.session_launcher"

_BACKUP_KEEP = 3


# ── Internal helpers ────────────────────────────────────────────────

def _find_pythonw() -> str:
    """Return path to pythonw.exe (Windows, no console) or fallback to python."""
    exe = Path(sys.executable)
    if sys.platform == "win32" and exe.name.lower() == "python.exe":
        candidate = exe.with_name("pythonw.exe")
        if candidate.is_file():
            return str(candidate).replace("\\", "/")
    return sys.executable.replace("\\", "/")


def _build_prep_command() -> str:
    """Hook command that runs prep silently on session start."""
    python_exe = sys.executable.replace("\\", "/")
    return (
        f'"{python_exe}" -m claude_backend prep '
        f'"${{CLAUDE_PROJECT_DIR:-.}}" --quiet || true'
    )


def _build_launcher_command() -> str:
    """Hook command that runs session_launcher (reads prefs, decides what to do)."""
    python_exe = _find_pythonw()
    return f'"{python_exe}" -m claude_backend.session_launcher || true'


# Backwards-compat alias for any external callers.
def _build_hook_command() -> str:
    return _build_prep_command()


def _atomic_write_text(path: Path, text: str, *, encoding: str = "utf-8") -> None:
    """Write `text` to `path` atomically: temp file + os.replace.

    On any exception, removes the temp file before re-raising. The target
    file is left untouched if the write fails partway.
    """
    tmp = path.with_suffix(path.suffix + ".tmp")
    try:
        tmp.write_text(text, encoding=encoding)
        os.replace(tmp, path)
    except OSError:
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass
        raise


def _prune_backups(keep: int = _BACKUP_KEEP) -> None:
    """Keep only the newest `keep` backups; unlink the rest. Best-effort."""
    try:
        backups = sorted(
            SETTINGS_PATH.parent.glob("settings.json.backup-*"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
    except OSError:
        return
    for old in backups[keep:]:
        try:
            old.unlink()
        except OSError as e:
            logger.debug("Failed to prune backup %s: %s", old, e)


def _make_backup() -> Path | None:
    """Timestamped copy of settings.json. Returns path on success, None on fail."""
    backup = SETTINGS_PATH.with_suffix(
        f".json.backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    )
    try:
        shutil.copy2(SETTINGS_PATH, backup)
        return backup
    except OSError as e:
        logger.warning("Backup failed: %s", e)
        return None


def _load_settings() -> tuple[dict | None, str]:
    """Load + parse settings.json. Returns (data, error_msg)."""
    if not SETTINGS_PATH.is_file():
        return None, f"settings.json not found at {SETTINGS_PATH}"
    try:
        text = SETTINGS_PATH.read_text(encoding="utf-8")
    except OSError as e:
        return None, f"Cannot read settings.json: {e}"
    try:
        return json.loads(text), ""
    except json.JSONDecodeError as e:
        return None, f"settings.json is not valid JSON: {e}"


def _save_settings(data: dict) -> tuple[bool, str]:
    """Backup, write atomically, prune old backups. Returns (ok, message)."""
    backup = _make_backup()
    try:
        new_text = json.dumps(data, indent=2, ensure_ascii=False)
        _atomic_write_text(SETTINGS_PATH, new_text)
    except OSError as e:
        if backup is not None:
            try:
                shutil.copy2(backup, SETTINGS_PATH)
            except OSError:
                pass
        return False, f"Cannot write settings.json: {e}"
    _prune_backups()
    msg = f"Backup saved at {backup.name}" if backup else "Wrote (no backup made)"
    return True, msg


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


def _check_hook(hook_id: str, legacy_substr: str | None) -> dict:
    """Generic status check for any hook id."""
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
    session_hooks = hooks.get("SessionStart", []) if isinstance(hooks, dict) else []
    if not isinstance(session_hooks, list):
        return status
    for entry in session_hooks:
        if not isinstance(entry, dict):
            continue
        for h in entry.get("hooks", []) or []:
            if _hook_matches(h, hook_id, legacy_substr):
                status["installed"] = True
                return status
    return status


def _install_hook(
    hook_id: str,
    description: str,
    command: str,
    legacy_substr: str | None,
) -> tuple[bool, str]:
    """Install a hook by id; deduplicates any existing matches first."""
    data, err = _load_settings()
    if data is None:
        return False, err

    if not isinstance(data, dict):
        return False, "settings.json must be a JSON object"

    hooks = data.setdefault("hooks", {})
    session_hooks = hooks.setdefault("SessionStart", [])
    if not isinstance(session_hooks, list):
        return False, "settings.json hooks.SessionStart must be a JSON array"

    # Dedupe: remove any existing entries matching this hook id (incl. legacy).
    session_hooks, removed = _filter_session_hooks(
        session_hooks, hook_id, legacy_substr,
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
    session_hooks.append(new_entry)
    hooks["SessionStart"] = session_hooks

    ok, msg = _save_settings(data)
    if not ok:
        return False, msg
    suffix = f" (replaced {removed} stale entr{'y' if removed == 1 else 'ies'})" if removed else ""
    return True, f"Installed!{suffix} {msg}"


def _uninstall_hook(hook_id: str, legacy_substr: str | None) -> tuple[bool, str]:
    """Remove a hook by id (with legacy fallback)."""
    data, err = _load_settings()
    if data is None:
        return False, err

    if not isinstance(data, dict):
        return False, "settings.json must be a JSON object"

    hooks = data.get("hooks", {})
    if not isinstance(hooks, dict):
        return False, "Hook not found (nothing to uninstall)"
    session_hooks = hooks.get("SessionStart", [])
    if not isinstance(session_hooks, list):
        return False, "Hook not found (nothing to uninstall)"

    filtered, removed = _filter_session_hooks(
        session_hooks, hook_id, legacy_substr,
    )

    if removed == 0:
        return False, "Hook not found (nothing to uninstall)"

    if filtered:
        hooks["SessionStart"] = filtered
    else:
        hooks.pop("SessionStart", None)
        if not hooks:
            data.pop("hooks", None)

    ok, msg = _save_settings(data)
    if not ok:
        return False, msg
    return True, f"Uninstalled {removed} entr{'y' if removed == 1 else 'ies'}. {msg}"


# ── Public API: Prep hook ───────────────────────────────────────────

def check_status() -> dict:
    """Status of the prep hook."""
    return _check_hook(HOOK_ID, _PREP_LEGACY_SUBSTR)


def install() -> tuple[bool, str]:
    """Install the prep hook. Deduplicates existing prep hooks first."""
    return _install_hook(
        HOOK_ID, HOOK_DESCRIPTION, _build_prep_command(), _PREP_LEGACY_SUBSTR,
    )


def uninstall() -> tuple[bool, str]:
    """Remove the prep hook."""
    return _uninstall_hook(HOOK_ID, _PREP_LEGACY_SUBSTR)


# ── Public API: Launcher hook ───────────────────────────────────────

def check_launcher_status() -> dict:
    """Status of the launcher hook."""
    return _check_hook(HOOK_ID_LAUNCH, _LAUNCH_LEGACY_SUBSTR)


def install_launcher_hook() -> tuple[bool, str]:
    """Install the launcher hook. Deduplicates existing launcher hooks first."""
    return _install_hook(
        HOOK_ID_LAUNCH,
        HOOK_DESC_LAUNCH,
        _build_launcher_command(),
        _LAUNCH_LEGACY_SUBSTR,
    )


def uninstall_launcher_hook() -> tuple[bool, str]:
    """Remove the launcher hook."""
    return _uninstall_hook(HOOK_ID_LAUNCH, _LAUNCH_LEGACY_SUBSTR)

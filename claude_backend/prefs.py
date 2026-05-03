"""User preferences for Token Saver GUI — small JSON store.

Stores UI prefs that persist across launches. Lives at
~/.claude/token_saver_prefs.json. Best-effort: any read/write
failure falls back to defaults so a corrupt file never bricks
the GUI.

Writes are atomic (temp file + os.replace) so a crash mid-save
leaves the previous file intact instead of producing a partial
JSON document. Eliminates the race window when GUI and tray
might both be saving prefs concurrently.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import asdict, dataclass, fields
from pathlib import Path

logger = logging.getLogger(__name__)

PREFS_PATH = Path.home() / ".claude" / "token_saver_prefs.json"


@dataclass
class Prefs:
    """User-facing preferences. Add fields here; defaults always backfilled."""
    show_welcome_on_launch: bool = True
    welcome_seen_count: int = 0
    last_project_path: str = ""
    show_tray_on_start: bool = False  # autostart hint, not enforced
    auto_launch_gui_on_session: bool = False  # opt-in: open GUI on Claude session
    auto_launch_minimized: bool = True  # if auto-launch on, prefer tray over window

    @classmethod
    def load(cls) -> "Prefs":
        """Load prefs. Missing file or bad JSON -> defaults."""
        if not PREFS_PATH.is_file():
            return cls()
        try:
            data = json.loads(PREFS_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("prefs load failed (%s); using defaults", e)
            return cls()
        if not isinstance(data, dict):
            return cls()
        # Filter to known fields only — forward-compat for new keys.
        valid = {f.name for f in fields(cls)}
        clean = {k: v for k, v in data.items() if k in valid}
        try:
            return cls(**clean)
        except TypeError as e:
            logger.warning("prefs schema mismatch (%s); using defaults", e)
            return cls()

    def save(self) -> bool:
        """Persist prefs atomically. Returns True on success."""
        try:
            PREFS_PATH.parent.mkdir(parents=True, exist_ok=True)
            text = json.dumps(asdict(self), indent=2)
            tmp = PREFS_PATH.with_suffix(PREFS_PATH.suffix + ".tmp")
            try:
                tmp.write_text(text, encoding="utf-8")
                os.replace(tmp, PREFS_PATH)
            except OSError:
                # Clean up temp file if rename failed.
                try:
                    tmp.unlink(missing_ok=True)
                except OSError:
                    pass
                raise
            return True
        except OSError as e:
            logger.warning("prefs save failed: %s", e)
            return False

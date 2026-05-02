"""User preferences for Token Saver GUI — small JSON store.

Stores UI prefs that persist across launches. Lives at
~/.claude/token_saver_prefs.json. Best-effort: any read/write
failure falls back to defaults so a corrupt file never bricks
the GUI.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field, fields
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
        # Filter to known fields only — forward-compat for new keys
        valid = {f.name for f in fields(cls)}
        clean = {k: v for k, v in data.items() if k in valid}
        try:
            return cls(**clean)
        except TypeError as e:
            logger.warning("prefs schema mismatch (%s); using defaults", e)
            return cls()

    def save(self) -> bool:
        """Persist prefs. Returns True on success."""
        try:
            PREFS_PATH.parent.mkdir(parents=True, exist_ok=True)
            PREFS_PATH.write_text(
                json.dumps(asdict(self), indent=2),
                encoding="utf-8",
            )
            return True
        except OSError as e:
            logger.warning("prefs save failed: %s", e)
            return False

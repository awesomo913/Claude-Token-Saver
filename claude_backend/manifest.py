"""Delta-aware manifest for tracking generated files with SHA-256 hashing."""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class ManifestEntry:
    """A single entry in the generation manifest."""
    path: str                # Relative path of generated file
    sha256: str              # Hash of generated content
    source_hash: str = ""    # Hash of source data that produced this file
    generator: str = ""      # Which generator made it
    generated_at: str = ""   # ISO timestamp
    version: int = 1


class Manifest:
    """Tracks generated files for delta updates."""

    def __init__(self, manifest_path: Path) -> None:
        self.path = manifest_path
        self._entries: dict[str, ManifestEntry] = {}
        self._load()

    def _load(self) -> None:
        """Load existing manifest from disk."""
        if not self.path.is_file():
            return
        try:
            for line in self.path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)
                entry = ManifestEntry(**{
                    k: v for k, v in data.items()
                    if k in ManifestEntry.__dataclass_fields__
                })
                self._entries[entry.path] = entry
            logger.debug("Loaded %d manifest entries from %s", len(self._entries), self.path)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Failed to load manifest %s: %s", self.path, e)

    def save(self) -> None:
        """Write manifest to disk."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            lines = [
                json.dumps(asdict(entry), ensure_ascii=False)
                for entry in self._entries.values()
            ]
            self.path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        except OSError as e:
            logger.warning("Failed to save manifest: %s", e)

    def needs_update(self, path: str, content: str, source_hash: str = "") -> bool:
        """Check if a generated file needs updating.

        Returns True if:
        - File not in manifest (new)
        - Source hash changed (source modified)
        - Generated content hash differs from manifest (we'd produce different output)
        """
        content_hash = _hash_str(content)
        entry = self._entries.get(path)
        if entry is None:
            return True
        if source_hash and entry.source_hash and source_hash != entry.source_hash:
            return True
        if entry.sha256 != content_hash:
            return True
        return False

    def is_user_modified(self, path: str, actual_path: Path) -> bool:
        """Check if a generated file was modified by the user after generation."""
        entry = self._entries.get(path)
        if entry is None:
            return False
        if not actual_path.is_file():
            return False
        actual_hash = _hash_str(actual_path.read_text(encoding="utf-8", errors="replace"))
        return actual_hash != entry.sha256

    def record(
        self,
        path: str,
        content: str,
        generator: str = "",
        source_hash: str = "",
    ) -> None:
        """Record a generated file in the manifest."""
        self._entries[path] = ManifestEntry(
            path=path,
            sha256=_hash_str(content),
            source_hash=source_hash,
            generator=generator,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    def get_entry(self, path: str) -> Optional[ManifestEntry]:
        return self._entries.get(path)

    def all_paths(self) -> list[str]:
        return list(self._entries.keys())

    def remove(self, path: str) -> None:
        self._entries.pop(path, None)

    def clear(self) -> None:
        self._entries.clear()


def _hash_str(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8", errors="replace")).hexdigest()

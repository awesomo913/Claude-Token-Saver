"""Project storage with pathlib, proper logging, and manifest tracking."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

from .types import FileEntry

logger = logging.getLogger(__name__)


class ProjectStorage:
    """Manages file storage for a Claude project directory."""

    def __init__(self, project_dir: Path) -> None:
        self.project_dir = project_dir
        self.project_dir.mkdir(parents=True, exist_ok=True)
        self.log_path = self.project_dir / "CLAUDE_LOG.jsonl"
        self.manifest_path = self.project_dir / "CLAUDE_MANIFEST.jsonl"

    def write_file(self, rel_path: str, content: str, source: str = "") -> bool:
        """Write content to a file under the project directory.

        Returns True if file was written, False if it already existed unchanged.
        """
        safe_parts = _normalize_path(rel_path)
        if not safe_parts:
            logger.warning("Skipping empty path: %r", rel_path)
            return False

        dest = self.project_dir
        for part in safe_parts[:-1]:
            dest = dest / part
        dest.mkdir(parents=True, exist_ok=True)
        dest = dest / safe_parts[-1]

        if dest.is_file():
            existing = dest.read_text(encoding="utf-8", errors="replace")
            if existing == content:
                self._log_event("skipped_unchanged", str(dest), source=source)
                return False

        dest.write_text(content, encoding="utf-8")
        self._log_event("file_written", str(dest), length=len(content), source=source)
        self._add_manifest(str(dest), source=source, length=len(content))
        return True

    def write_entry(self, entry: FileEntry) -> bool:
        """Write a FileEntry to the project directory."""
        return self.write_file(entry.path, entry.content, source=entry.source)

    def list_files(self) -> list[str]:
        """List all files in the project directory (relative paths)."""
        result = []
        for p in sorted(self.project_dir.rglob("*")):
            if p.is_file() and p.name not in ("CLAUDE_LOG.jsonl", "CLAUDE_MANIFEST.jsonl"):
                try:
                    result.append(str(p.relative_to(self.project_dir)))
                except ValueError:
                    result.append(str(p))
        return result

    def _log_event(self, event: str, path: str, **extra: object) -> None:
        """Append an event to the log file."""
        entry = {"event": event, "path": path, "ts": _now_iso(), **extra}
        try:
            with self.log_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except OSError as e:
            logger.warning("Failed to write log: %s", e)

    def _add_manifest(self, path: str, **extra: object) -> None:
        """Append an entry to the manifest."""
        entry = {"path": path, "ts": _now_iso(), **extra}
        try:
            with self.manifest_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except OSError as e:
            logger.warning("Failed to write manifest: %s", e)


def _normalize_path(rel_path: str) -> list[str]:
    """Normalize a relative or absolute path into clean segments.

    Handles Windows drive letters, mixed separators, and path traversal.
    """
    p = rel_path.replace("\\", "/")

    # Strip Windows drive letter (e.g., "C:/Users/..." -> "Users/...")
    if len(p) >= 2 and p[1] == ":":
        p = p[2:]

    # Split and filter dangerous/empty segments
    parts = [
        seg for seg in PurePosixPath(p).parts
        if seg not in (".", "..", "/", "") and seg != "/"
    ]
    return parts


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

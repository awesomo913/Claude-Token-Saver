"""Local filesystem scanner for additional source directories."""

from __future__ import annotations

import logging
from pathlib import Path

from ..types import FileEntry

logger = logging.getLogger(__name__)


def scan_local_sources(sources: list[dict], default_extensions: list[str]) -> list[FileEntry]:
    """Scan configured local source directories.

    Each source dict should have:
        paths: list of directory paths to scan
        extensions: optional list of extensions (uses default if missing)
    """
    entries: list[FileEntry] = []

    for source in sources:
        paths = source.get("paths", [])
        extensions = source.get("extensions", default_extensions)
        ext_set = set(extensions)

        for dir_path_str in paths:
            dir_path = Path(dir_path_str).resolve()
            if not dir_path.is_dir():
                logger.debug("Local source directory not found: %s", dir_path)
                continue

            count = 0
            for path in sorted(dir_path.rglob("*")):
                if not path.is_file():
                    continue
                if path.suffix not in ext_set:
                    continue

                try:
                    content = path.read_text(encoding="utf-8", errors="replace")
                except (OSError, UnicodeDecodeError) as e:
                    logger.debug("Could not read %s: %s", path, e)
                    continue

                rel = path.relative_to(dir_path)
                entries.append(FileEntry(
                    path=str(rel).replace("\\", "/"),
                    content=content,
                    ext=path.suffix,
                    source=f"local:{dir_path.name}",
                    abs_path=path,
                ))
                count += 1

            logger.info("Scanned %d files from %s", count, dir_path)

    return entries

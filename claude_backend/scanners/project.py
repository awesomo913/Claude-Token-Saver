"""Project scanner: discovers and catalogs all files in a target project.

Optimized for large repos (10K+ files):
- Uses os.scandir walk with early directory pruning (not rglob)
- Binary detection on first 512 bytes (not 8K)
- Lazy content loading only for files that pass all filters
- Ignore-set lookup is O(1) per directory, not O(n) per file
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

from ..config import ScanConfig
from ..types import FileEntry

logger = logging.getLogger(__name__)

BINARY_CHECK_SIZE = 512


def _build_dir_filter(config: ScanConfig):
    """Build a predicate that returns True if a directory name should be skipped.

    Pre-computes the ignore-sets from config so O(1) lookup per directory.
    """
    exact_ignore = set()
    glob_suffixes: list[str] = []
    for pat in config.ignore_dirs:
        if pat.startswith("*"):
            glob_suffixes.append(pat[1:])
        else:
            exact_ignore.add(pat)

    def should_skip(name: str) -> bool:
        if name in exact_ignore:
            return True
        if any(name.endswith(suf) for suf in glob_suffixes):
            return True
        if name.startswith(".") and name not in (".", ".claude"):
            return True
        return False

    return should_skip


def scan_project(root: Path, config: ScanConfig) -> list[FileEntry]:
    """Scan a project directory and return all matching files.

    Uses os.scandir + manual walk for performance on large repos.
    Prunes ignored directories early so we never descend into
    node_modules, .git, __pycache__, etc.
    """
    root = root.resolve()
    if not root.is_dir():
        logger.error("Project root is not a directory: %s", root)
        return []

    entries: list[FileEntry] = []
    ext_set = set(config.extensions)
    max_bytes = config.max_file_size_kb * 1024
    max_files = config.max_files

    should_skip_dir = _build_dir_filter(config)

    root_str = str(root)

    # Manual os.scandir walk — 3-5x faster than Path.rglob on Windows
    stack: list[str] = [root_str]
    while stack and len(entries) < max_files:
        current = stack.pop()
        try:
            scanner = os.scandir(current)
        except (PermissionError, OSError):
            continue

        subdirs: list[str] = []
        with scanner:
            for item in scanner:
                if len(entries) >= max_files:
                    break

                name = item.name

                if item.is_dir(follow_symlinks=False):
                    # Prune ignored directories BEFORE descending
                    if should_skip_dir(name):
                        continue
                    subdirs.append(item.path)
                    continue

                if not item.is_file(follow_symlinks=False):
                    continue

                # Extension check (fast string op)
                dot_idx = name.rfind(".")
                if dot_idx <= 0:
                    continue
                ext = name[dot_idx:]
                if ext not in ext_set:
                    continue

                # Size check
                try:
                    stat = item.stat()
                    if stat.st_size > max_bytes or stat.st_size == 0:
                        continue
                except OSError:
                    continue

                # Binary check (first 512 bytes only)
                full_path = item.path
                try:
                    with open(full_path, "rb") as f:
                        chunk = f.read(BINARY_CHECK_SIZE)
                    if b"\x00" in chunk:
                        continue
                except OSError:
                    continue

                # Read content (only files that passed ALL filters)
                try:
                    with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                        content = f.read()
                except OSError:
                    continue

                # Compute relative path
                try:
                    rel = os.path.relpath(full_path, root_str).replace("\\", "/")
                except ValueError:
                    rel = name

                entries.append(FileEntry(
                    path=rel,
                    content=content,
                    ext=ext,
                    source="local",
                    abs_path=Path(full_path),
                ))

        # Add subdirs to stack (sorted for deterministic order)
        stack.extend(sorted(subdirs, reverse=True))

    if len(entries) >= max_files:
        logger.info("Reached max_files limit (%d), stopped scanning", max_files)
    logger.info("Scanned %d files in %s", len(entries), root)
    return entries


def scan_project_fast_mtimes(root: Path, config: ScanConfig) -> dict[str, float]:
    """Fast scan that only returns {relative_path: mtime} without reading content.

    Used by auto-scan to detect changes without re-reading all files.
    ~10x faster than full scan on large repos.
    """
    root = root.resolve()
    if not root.is_dir():
        return {}

    ext_set = set(config.extensions)
    should_skip_dir = _build_dir_filter(config)

    root_str = str(root)
    mtimes: dict[str, float] = {}
    stack: list[str] = [root_str]

    while stack:
        current = stack.pop()
        try:
            scanner = os.scandir(current)
        except (PermissionError, OSError):
            continue
        with scanner:
            for item in scanner:
                name = item.name
                if item.is_dir(follow_symlinks=False):
                    if should_skip_dir(name):
                        continue
                    stack.append(item.path)
                    continue
                if not item.is_file(follow_symlinks=False):
                    continue
                dot_idx = name.rfind(".")
                if dot_idx <= 0:
                    continue
                if name[dot_idx:] not in ext_set:
                    continue
                try:
                    st = item.stat()
                    rel = os.path.relpath(item.path, root_str).replace("\\", "/")
                    mtimes[rel] = st.st_mtime
                except (OSError, ValueError):
                    continue

    return mtimes


def get_language_stats(entries: list[FileEntry]) -> dict[str, int]:
    """Count files by extension."""
    stats: dict[str, int] = {}
    for e in entries:
        stats[e.ext] = stats.get(e.ext, 0) + 1
    return dict(sorted(stats.items(), key=lambda x: -x[1]))


def find_entry_points(entries: list[FileEntry]) -> list[str]:
    """Find likely entry point files."""
    markers = ["if __name__", "def main(", "app.mainloop(", "app.run("]
    result = []
    for e in entries:
        if any(m in e.content for m in markers):
            result.append(e.path)
    return result


def find_key_files(root: Path) -> list[str]:
    """Find important project files that exist at the root."""
    names = [
        "README.md", "README.rst", "README.txt",
        "CLAUDE.md", "setup.py", "setup.cfg",
        "pyproject.toml", "package.json", "Cargo.toml",
        "requirements.txt", "Makefile", "Dockerfile",
        ".gitignore",
    ]
    found = []
    for name in names:
        if (root / name).is_file():
            found.append(name)
    return found


def find_dependencies(root: Path) -> list[str]:
    """Extract dependency names from requirements.txt or pyproject.toml."""
    deps: list[str] = []

    req = root / "requirements.txt"
    if req.is_file():
        try:
            for line in req.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and not line.startswith("-"):
                    name = line.split(">=")[0].split("==")[0].split("<")[0].split("[")[0].strip()
                    if name:
                        deps.append(name)
        except OSError:
            pass

    pyproject = root / "pyproject.toml"
    if pyproject.is_file():
        try:
            text = pyproject.read_text(encoding="utf-8")
            in_deps = False
            for line in text.splitlines():
                stripped = line.strip()
                if stripped.startswith("dependencies"):
                    in_deps = True
                    continue
                if in_deps:
                    if stripped.startswith("]"):
                        in_deps = False
                        continue
                    if stripped.startswith('"') or stripped.startswith("'"):
                        name = stripped.strip("\"', ")
                        name = name.split(">=")[0].split("==")[0].split("<")[0].split("[")[0].strip()
                        if name:
                            deps.append(name)
        except OSError:
            pass

    return deps

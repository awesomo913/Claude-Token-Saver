"""Configuration loading with layered defaults."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

DEFAULT_EXTENSIONS = [".py", ".js", ".ts", ".tsx", ".jsx", ".md", ".json", ".toml"]
DEFAULT_IGNORE_DIRS = [
    ".git", "__pycache__", "node_modules", ".venv", "venv", ".env",
    ".tox", ".mypy_cache", ".pytest_cache", "dist", "build", "*.egg-info",
    ".claude",
]


@dataclass
class ScanConfig:
    """Configuration for scanning and generation."""
    max_file_size_kb: int = 1024
    max_files: int = 500
    extensions: list[str] = field(default_factory=lambda: list(DEFAULT_EXTENSIONS))
    ignore_dirs: list[str] = field(default_factory=lambda: list(DEFAULT_IGNORE_DIRS))

    generate_claude_md: bool = True
    generate_memory: bool = True
    generate_snippets: bool = True
    claude_md_max_lines: int = 200
    max_snippet_lines: int = 50
    snippet_min_reuse: int = 1  # minimum cross-file references to include

    github_enabled: bool = False
    github_token: str = ""
    github_sources: list[dict] = field(default_factory=list)

    local_sources: list[dict] = field(default_factory=list)


def load_config(
    config_path: Optional[Path] = None,
    project_path: Optional[Path] = None,
) -> ScanConfig:
    """Load config with layered defaults.

    Priority: built-in defaults < global < project < explicit path.
    """
    merged: dict = {}

    # Layer 1: global config
    global_cfg = Path.home() / ".claude" / "backend_config.json"
    if global_cfg.is_file():
        merged.update(_load_json(global_cfg))

    # Layer 2: project config
    if project_path:
        project_cfg = project_path / ".claude" / "backend_config.json"
        if project_cfg.is_file():
            merged.update(_load_json(project_cfg))

    # Layer 3: explicit config file
    if config_path and config_path.is_file():
        merged.update(_load_json(config_path))

    return _dict_to_config(merged)


def _load_json(path: Path) -> dict:
    """Load a JSON config file, return empty dict on failure."""
    try:
        text = path.read_text(encoding="utf-8")
        data = json.loads(text)
        if isinstance(data, dict):
            logger.debug("Loaded config from %s", path)
            return data
        logger.warning("Config at %s is not a JSON object, ignoring", path)
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Failed to load config %s: %s", path, e)
    return {}


def _dict_to_config(data: dict) -> ScanConfig:
    """Convert a dict to ScanConfig, ignoring unknown keys."""
    known = {f.name for f in ScanConfig.__dataclass_fields__.values()}
    filtered = {k: v for k, v in data.items() if k in known}
    return ScanConfig(**filtered)


def save_config_example(path: Path) -> None:
    """Write a config example to disk."""
    example = asdict(ScanConfig())
    path.write_text(
        json.dumps(example, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    logger.info("Wrote config example to %s", path)

"""Configuration management for Gemini Coder."""

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

from .platform_utils import get_config_dir


@dataclass
class AppConfig:
    """Application configuration."""
    theme: str = "dark"
    window_width: int = 1200
    window_height: int = 800
    auto_scroll: bool = True
    task_default_minutes: int = 3
    expand_depth_limit: int = 3
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    gemini_temperature: float = 0.9
    auto_save_enabled: bool = True


class ConfigManager:
    """Manages application configuration with persistence."""

    def __init__(self) -> None:
        self._path = get_config_dir() / "config.json"
        self.config = self._load()

    def _load(self) -> AppConfig:
        """Load configuration from disk."""
        if self._path.exists():
            try:
                data = json.loads(self._path.read_text(encoding="utf-8"))
                known = {f.name for f in AppConfig.__dataclass_fields__.values()}
                filtered = {k: v for k, v in data.items() if k in known}
                return AppConfig(**filtered)
            except Exception:
                pass
        return AppConfig()

    def save(self) -> None:
        """Save configuration to disk."""
        data = asdict(self.config)
        self._path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def update(self, **kwargs) -> None:
        """Update configuration fields."""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        self.save()

    def get(self, key: str, default=None):
        """Get a configuration value."""
        return getattr(self.config, key, default)

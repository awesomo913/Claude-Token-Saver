# From: gemini_coder/config.py:26

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

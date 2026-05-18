# From: gemini_coder/config.py:33
# Load configuration from disk.

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

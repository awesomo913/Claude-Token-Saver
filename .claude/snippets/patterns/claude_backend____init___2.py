# From: claude_backend/manifest.py:30

    def __init__(self, manifest_path: Path) -> None:
        self.path = manifest_path
        self._entries: dict[str, ManifestEntry] = {}
        self._load()

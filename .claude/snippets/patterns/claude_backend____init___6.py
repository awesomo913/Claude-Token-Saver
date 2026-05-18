# From: claude_backend/storage.py:18

    def __init__(self, project_dir: Path) -> None:
        self.project_dir = project_dir
        self.project_dir.mkdir(parents=True, exist_ok=True)
        self.log_path = self.project_dir / "CLAUDE_LOG.jsonl"
        self.manifest_path = self.project_dir / "CLAUDE_MANIFEST.jsonl"

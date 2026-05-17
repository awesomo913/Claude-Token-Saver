# From: claude_backend/backend.py:232
# Report what's generated and its freshness.

    def status(self, project_path: Path) -> dict:
        """Report what's generated and its freshness."""
        project_path = project_path.resolve()
        info: dict = {"project": project_path.name, "path": str(project_path)}

        claude_md = project_path / "CLAUDE.md"
        info["claude_md"] = claude_md.is_file()

        memory_dir = project_path / ".claude" / "memory"
        if memory_dir.is_dir():
            info["memory_files"] = [f.name for f in memory_dir.iterdir() if f.is_file()]
        else:
            info["memory_files"] = []

        snippets_dir = project_path / ".claude" / "snippets"
        if snippets_dir.is_dir():
            count = sum(1 for f in snippets_dir.rglob("*") if f.is_file())
            info["snippet_count"] = count
        else:
            info["snippet_count"] = 0

        manifest_path = project_path / ".claude" / "manifest.jsonl"
        info["has_manifest"] = manifest_path.is_file()

        return info

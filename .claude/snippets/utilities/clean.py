# From: claude_backend/backend.py:258
# Remove generated artifacts.

    def clean(self, project_path: Path) -> list[str]:
        """Remove generated artifacts."""
        project_path = project_path.resolve()
        removed: list[str] = []

        # Remove generated section from CLAUDE.md
        claude_md = project_path / "CLAUDE.md"
        if claude_md.is_file():
            from .generators.claude_md import MARKER_START, MARKER_END
            content = claude_md.read_text(encoding="utf-8", errors="replace")
            start = content.find(MARKER_START)
            end = content.find(MARKER_END)
            if start != -1 and end != -1:
                end += len(MARKER_END)
                new_content = (content[:start] + content[end:]).strip()
                if new_content:
                    claude_md.write_text(new_content + "\n", encoding="utf-8")
                else:
                    claude_md.unlink()
                removed.append(str(claude_md))

        # Remove .claude/memory, .claude/snippets, .claude/manifest.jsonl
        for subdir in ["memory", "snippets"]:
            target = project_path / ".claude" / subdir
            if target.is_dir():
                import shutil
                shutil.rmtree(target)
                removed.append(str(target))

        manifest = project_path / ".claude" / "manifest.jsonl"
        if manifest.is_file():
            manifest.unlink()
            removed.append(str(manifest))

        logger.info("Cleaned %d items", len(removed))
        return removed

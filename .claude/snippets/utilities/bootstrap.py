# From: claude_backend/backend.py:80
# Full scan + generate all context files.

    def bootstrap(self, project_path: Path) -> GenerationResult:
        """Full scan + generate all context files."""
        analysis = self.analyze(project_path)
        result = GenerationResult()

        logger.info(
            "Analysis: %d files, %d modules, %d code blocks",
            len(analysis.files), len(analysis.modules), len(analysis.blocks),
        )

        # Generate CLAUDE.md
        if self.config.generate_claude_md:
            try:
                wrote = write_claude_md(analysis, self.config.claude_md_max_lines)
                path = str(analysis.root / "CLAUDE.md")
                if wrote:
                    result.files_written.append(path)
                else:
                    result.files_skipped.append(path)
            except Exception as e:
                logger.error("Failed to generate CLAUDE.md: %s", e)
                result.errors.append(f"CLAUDE.md: {e}")

        # Generate memory files
        if self.config.generate_memory:
            try:
                written = write_memory_files(analysis)
                result.files_written.extend(written)
            except Exception as e:
                logger.error("Failed to generate memory files: %s", e)
                result.errors.append(f"memory: {e}")

        # Generate snippet library
        if self.config.generate_snippets:
            try:
                written = write_snippet_library(analysis, self.config.max_snippet_lines)
                result.files_written.extend(written)
            except Exception as e:
                logger.error("Failed to generate snippets: %s", e)
                result.errors.append(f"snippets: {e}")

        # Save manifest
        manifest_path = project_path / ".claude" / "manifest.jsonl"
        manifest = Manifest(manifest_path)
        for f in result.files_written:
            manifest.record(f, content="", generator="bootstrap")
        manifest.save()

        logger.info("Bootstrap complete: %s", result.summary)
        return result

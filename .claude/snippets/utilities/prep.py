# From: claude_backend/backend.py:131
# Delta update: only regenerate outputs whose source files changed.

    def prep(self, project_path: Path, force: bool = False) -> GenerationResult:
        """Delta update: only regenerate outputs whose source files changed.

        Uses manifest SHA-256 hashes to skip unchanged generators.

        Args:
            project_path: project to prep
            force: bypass the source-snapshot delta check and regenerate
                everything. Useful after upgrading Token Saver (new
                generators may produce files that didn't exist before).
        """
        manifest_path = project_path / ".claude" / "manifest.jsonl"
        manifest = Manifest(manifest_path)

        # Hash current source files to detect changes
        from .scanners.project import scan_project_fast_mtimes
        current_mtimes = scan_project_fast_mtimes(project_path, self.config)

        # Compare against last prep's source snapshot (skipped on force).
        last_snapshot_path = project_path / ".claude" / "source_snapshot.json"
        source_changed = True
        if not force and last_snapshot_path.is_file():
            import json
            try:
                old = json.loads(last_snapshot_path.read_text(encoding="utf-8"))
                source_changed = (old != current_mtimes)
            except (json.JSONDecodeError, OSError):
                pass

        result = GenerationResult()

        if not source_changed:
            logger.info("Prep: no source files changed, skipping regeneration")
            result.files_skipped.append("(all outputs unchanged)")
            return result

        # Source changed — do full analysis and regenerate
        analysis = self.analyze(project_path)

        if self.config.generate_claude_md:
            try:
                content = generate_claude_md(analysis, self.config.claude_md_max_lines)
                path_str = str(analysis.root / "CLAUDE.md")
                if manifest.needs_update(path_str, content):
                    write_claude_md(analysis, self.config.claude_md_max_lines)
                    manifest.record(path_str, content=content, generator="prep")
                    result.files_updated.append(path_str)
                else:
                    result.files_skipped.append(path_str)
            except Exception as e:
                result.errors.append(f"CLAUDE.md: {e}")

        if self.config.generate_memory:
            try:
                from .generators.memory_files import generate_memory_files, get_memory_dirs
                files = generate_memory_files(analysis)
                claude_dir, project_dir = get_memory_dirs(analysis.root)
                for target_dir in [claude_dir, project_dir]:
                    target_dir.mkdir(parents=True, exist_ok=True)
                    for filename, content in files.items():
                        path_str = str(target_dir / filename)
                        if manifest.needs_update(path_str, content):
                            (target_dir / filename).write_text(content, encoding="utf-8")
                            manifest.record(path_str, content=content, generator="prep")
                            result.files_updated.append(path_str)
                        else:
                            result.files_skipped.append(path_str)
            except Exception as e:
                result.errors.append(f"memory: {e}")

        if self.config.generate_snippets:
            try:
                from .generators.snippet_library import generate_snippet_library
                snippets = generate_snippet_library(analysis, self.config.max_snippet_lines)
                base = analysis.root / ".claude" / "snippets"
                for rel_path, content in snippets.items():
                    full = base / rel_path
                    path_str = str(full)
                    if manifest.needs_update(path_str, content):
                        full.parent.mkdir(parents=True, exist_ok=True)
                        full.write_text(content, encoding="utf-8")
                        manifest.record(path_str, content=content, generator="prep")
                        result.files_updated.append(path_str)
                    else:
                        result.files_skipped.append(path_str)
            except Exception as e:
                result.errors.append(f"snippets: {e}")

        manifest.save()

        # Save source snapshot for next delta check
        import json
        last_snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        last_snapshot_path.write_text(
            json.dumps(current_mtimes, ensure_ascii=False),
            encoding="utf-8",
        )

        logger.info("Prep complete: %s", result.summary)
        return result

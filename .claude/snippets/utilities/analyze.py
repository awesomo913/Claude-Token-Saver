# From: claude_backend/backend.py:38
# Scan and analyze a project without generating anything.

    def analyze(self, project_path: Path) -> ProjectAnalysis:
        """Scan and analyze a project without generating anything."""
        project_path = project_path.resolve()
        name = project_path.name

        logger.info("Scanning %s ...", project_path)
        entries = scan_project(project_path, self.config)

        logger.info("Analyzing %d files ...", len(entries))
        lang_stats = get_language_stats(entries)
        entry_points = find_entry_points(entries)
        key_files = find_key_files(project_path)
        dependencies = find_dependencies(project_path)
        modules = map_modules(entries, name)
        conventions = detect_conventions(entries)

        # Extract code blocks from all supported files
        all_blocks = []
        for entry in entries:
            blocks = extract_blocks(entry.content, entry.ext, entry.path)
            all_blocks.extend(blocks)

        # Check for existing CLAUDE.md
        claude_md = project_path / "CLAUDE.md"
        existing_content = None
        if claude_md.is_file():
            existing_content = claude_md.read_text(encoding="utf-8", errors="replace")

        return ProjectAnalysis(
            root=project_path,
            name=name,
            files=entries,
            modules=modules,
            conventions=conventions,
            language_stats=lang_stats,
            entry_points=entry_points,
            dependencies=dependencies,
            key_files=key_files,
            existing_claude_md=existing_content,
            blocks=all_blocks,
        )

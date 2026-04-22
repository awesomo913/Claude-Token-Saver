"""ClaudeContextManager: orchestrates scanning, analysis, and generation."""

from __future__ import annotations

import json
import logging
import shutil
from pathlib import Path
from typing import Optional

from .config import ScanConfig
from .manifest import Manifest
from .types import GenerationResult, ProjectAnalysis

from .scanners.project import (
    find_dependencies,
    find_entry_points,
    find_key_files,
    get_language_stats,
    scan_project,
    scan_project_fast_mtimes,
)
from .analyzers.code_extractor import extract_blocks
from .analyzers.pattern_detector import detect_conventions
from .analyzers.structure_mapper import map_modules

from .generators.claude_md import MARKER_START, MARKER_END, generate_claude_md, write_claude_md
from .generators.memory_files import generate_memory_files, get_memory_dirs, write_memory_files
from .generators.snippet_library import generate_snippet_library, write_snippet_library

logger = logging.getLogger(__name__)


class ClaudeContextManager:
    """Main orchestrator for the Claude token saver."""

    def __init__(self, config: Optional[ScanConfig] = None) -> None:
        self.config = config or ScanConfig()

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

        # Save manifest with actual content hashes so delta prep works correctly
        manifest_path = project_path / ".claude" / "manifest.jsonl"
        manifest = Manifest(manifest_path)
        for f in result.files_written:
            try:
                content = Path(f).read_text(encoding="utf-8", errors="replace")
            except OSError:
                content = ""
            manifest.record(f, content=content, generator="bootstrap")
        manifest.save()

        logger.info("Bootstrap complete: %s", result.summary)
        return result

    def prep(self, project_path: Path) -> GenerationResult:
        """Delta update: only regenerate outputs whose source files changed.

        Uses manifest SHA-256 hashes to skip unchanged generators.
        """
        manifest_path = project_path / ".claude" / "manifest.jsonl"
        manifest = Manifest(manifest_path)

        # Hash current source files to detect changes
        current_mtimes = scan_project_fast_mtimes(project_path, self.config)

        # Compare against last prep's source snapshot
        last_snapshot_path = project_path / ".claude" / "source_snapshot.json"
        source_changed = True
        if last_snapshot_path.is_file():
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
        last_snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        last_snapshot_path.write_text(
            json.dumps(current_mtimes, ensure_ascii=False),
            encoding="utf-8",
        )

        logger.info("Prep complete: %s", result.summary)
        return result

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

    def clean(self, project_path: Path) -> list[str]:
        """Remove generated artifacts."""
        project_path = project_path.resolve()
        removed: list[str] = []

        # Remove generated section from CLAUDE.md
        claude_md = project_path / "CLAUDE.md"
        if claude_md.is_file():
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
                shutil.rmtree(target)
                removed.append(str(target))

        manifest = project_path / ".claude" / "manifest.jsonl"
        if manifest.is_file():
            manifest.unlink()
            removed.append(str(manifest))

        logger.info("Cleaned %d items", len(removed))
        return removed

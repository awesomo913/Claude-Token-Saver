"""Shared data types for claude_backend."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class FileEntry:
    """A discovered file from any scanner."""
    path: str              # Relative path from scan root
    content: str           # File content
    ext: str               # Extension including dot, e.g. ".py"
    source: str = ""       # Origin label: "local", "github:owner/repo", "ai"
    abs_path: Optional[Path] = None

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.content.encode("utf-8", errors="replace")).hexdigest()

    @property
    def line_count(self) -> int:
        return self.content.count("\n") + 1


@dataclass
class CodeBlock:
    """An extracted code block (function, class, etc.)."""
    name: str
    kind: str              # "function", "async_function", "class", "method", "js_function"
    source: str            # Extracted source text
    start_line: int
    end_line: int
    docstring: Optional[str] = None
    decorators: list[str] = field(default_factory=list)
    file_path: str = ""


@dataclass
class ModuleInfo:
    """Information about a Python module."""
    path: str              # Relative path from project root
    docstring: Optional[str] = None
    public_names: list[str] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)      # Internal imports
    entry_point: bool = False
    line_count: int = 0


@dataclass
class ConventionReport:
    """Detected coding conventions."""
    path_style: str = "unknown"       # "pathlib", "os.path", "mixed", "none"
    type_hints: str = "unknown"       # "heavy", "light", "none"
    string_format: str = "unknown"    # "f-string", "format", "percent", "mixed"
    error_handling: str = "unknown"   # "specific", "bare", "mixed", "none"
    logging_style: str = "unknown"    # "logging", "print", "mixed", "none"
    import_style: str = "unknown"     # "absolute", "relative", "mixed"
    samples_analyzed: int = 0
    details: dict = field(default_factory=dict)


@dataclass
class ProjectAnalysis:
    """Complete analysis of a project."""
    root: Path
    name: str
    files: list[FileEntry] = field(default_factory=list)
    modules: list[ModuleInfo] = field(default_factory=list)
    conventions: ConventionReport = field(default_factory=ConventionReport)
    language_stats: dict[str, int] = field(default_factory=dict)
    entry_points: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    key_files: list[str] = field(default_factory=list)
    existing_claude_md: Optional[str] = None
    blocks: list[CodeBlock] = field(default_factory=list)


@dataclass
class GenerationResult:
    """Result of a generation run."""
    files_written: list[str] = field(default_factory=list)
    files_skipped: list[str] = field(default_factory=list)
    files_updated: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def summary(self) -> str:
        parts = []
        if self.files_written:
            parts.append(f"{len(self.files_written)} new")
        if self.files_updated:
            parts.append(f"{len(self.files_updated)} updated")
        if self.files_skipped:
            parts.append(f"{len(self.files_skipped)} unchanged")
        if self.errors:
            parts.append(f"{len(self.errors)} errors")
        return ", ".join(parts) or "nothing to do"

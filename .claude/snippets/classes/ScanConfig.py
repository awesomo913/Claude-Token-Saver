# From: claude_backend/config.py:21

@dataclass
class ScanConfig:
    """Configuration for scanning and generation."""
    max_file_size_kb: int = 1024
    max_files: int = 500
    extensions: list[str] = field(default_factory=lambda: list(DEFAULT_EXTENSIONS))
    ignore_dirs: list[str] = field(default_factory=lambda: list(DEFAULT_IGNORE_DIRS))

    generate_claude_md: bool = True
    generate_memory: bool = True
    generate_snippets: bool = True
    claude_md_max_lines: int = 200
    max_snippet_lines: int = 50
    snippet_min_reuse: int = 1  # minimum cross-file references to include

    github_enabled: bool = False
    github_token: str = ""
    github_sources: list[dict] = field(default_factory=list)

    local_sources: list[dict] = field(default_factory=list)

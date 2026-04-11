# From: claude_backend/types.py:66

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

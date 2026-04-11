# From: claude_backend/types.py:42

@dataclass
class ModuleInfo:
    """Information about a Python module."""
    path: str              # Relative path from project root
    docstring: Optional[str] = None
    public_names: list[str] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)      # Internal imports
    entry_point: bool = False
    line_count: int = 0

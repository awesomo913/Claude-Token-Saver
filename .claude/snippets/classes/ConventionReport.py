# From: claude_backend/types.py:53

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

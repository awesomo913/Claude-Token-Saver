# From: claude_backend/types.py:11

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

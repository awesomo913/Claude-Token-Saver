# From: claude_backend/types.py:82

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

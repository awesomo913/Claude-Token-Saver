# From: claude_backend/manifest.py:16

@dataclass
class ManifestEntry:
    """A single entry in the generation manifest."""
    path: str                # Relative path of generated file
    sha256: str              # Hash of generated content
    source_hash: str = ""    # Hash of source data that produced this file
    generator: str = ""      # Which generator made it
    generated_at: str = ""   # ISO timestamp
    version: int = 1

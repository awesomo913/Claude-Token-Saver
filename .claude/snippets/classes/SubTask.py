# From: classifier/types.py:22

@dataclass
class SubTask:
    """A single decomposed piece of a prompt."""
    text: str
    routing: str                     # "free" or "claude"
    task_type: str                   # from classification
    estimated_tokens: int = 0

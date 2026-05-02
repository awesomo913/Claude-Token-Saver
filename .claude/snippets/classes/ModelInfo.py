# From: classifier/types.py:43

@dataclass
class ModelInfo:
    """Description of an available model."""
    id: str
    name: str
    context_length: int = 0
    is_free: bool = False
    provider: str = ""

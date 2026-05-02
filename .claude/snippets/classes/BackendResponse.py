# From: classifier/types.py:53

@dataclass
class BackendResponse:
    """Response from any AI backend."""
    text: str
    model: str
    backend: str
    input_tokens: int = 0
    output_tokens: int = 0
    elapsed_sec: float = 0.0
    error: str = ""

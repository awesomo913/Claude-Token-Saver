# From: classifier/types.py:65

@dataclass
class SavingsEvent:
    """Single routing event for the tracker."""
    timestamp: str
    original_tokens: int
    free_tokens_sent: int
    claude_tokens_needed: int
    tokens_saved: int
    cost_saved_usd: float
    backend_used: str
    model_used: str
    routing_decision: str
    task_types: list[str]
    elapsed_sec: float = 0.0
    prompt_preview: str = ""  # first 200 chars of original prompt

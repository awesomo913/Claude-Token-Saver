# From: classifier/types.py:9

@dataclass
class TaskClassification:
    """Result of classifying a prompt."""
    complexity_score: float          # 0.0 (trivial) to 1.0 (expert-level)
    task_types: list[str]            # detected task categories
    domains: list[str]               # detected technical domains
    routing: str                     # "free", "claude", "split"
    confidence: float                # 0.0–1.0
    reasoning: str                   # human-readable explanation
    estimated_free_pct: float        # 0.0–1.0 how much can go to free models
    signal_details: dict[str, Any] = field(default_factory=dict)

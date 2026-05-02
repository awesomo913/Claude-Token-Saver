# From: classifier/types.py:82

@dataclass
class SavingsSummary:
    """Aggregate savings stats."""
    total_prompts: int = 0
    tokens_sent_to_free: int = 0
    tokens_sent_to_claude: int = 0
    tokens_avoided: int = 0
    estimated_cost_saved: float = 0.0
    avg_free_pct: float = 0.0
    by_backend: dict[str, int] = field(default_factory=dict)
    by_task_type: dict[str, int] = field(default_factory=dict)

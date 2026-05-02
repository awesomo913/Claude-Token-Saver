# From: classifier/types.py:31

@dataclass
class RoutingResult:
    """Complete routing output from the splitter."""
    original_prompt: str
    subtasks: list[SubTask]
    free_prompt: str                 # assembled prompt for free models
    claude_prompt: str               # trimmed prompt for Claude
    free_token_estimate: int = 0
    claude_token_estimate: int = 0
    savings_pct: float = 0.0

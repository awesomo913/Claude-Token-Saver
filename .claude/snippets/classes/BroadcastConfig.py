# From: broadcast.py:166

@dataclass
class BroadcastConfig:
    """Configuration for a broadcast run."""
    task: str = ""
    build_target: str = "PC Desktop App"
    enhancements: list[str] = field(default_factory=lambda: ["More Features + Robustness"])
    context: str = ""
    session_ids: list[str] = field(default_factory=list)  # Empty = all active
    endless: bool = True
    max_iterations: int = 999  # Safety cap
    time_limit_minutes: int = 0  # 0 = no limit
    smart_route: bool = False  # Classify + split: free parts → Gemini, hard → Claude

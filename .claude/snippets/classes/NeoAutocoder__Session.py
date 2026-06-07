# From: NeoAutocoder/session.py:9
# Exact match to original Session dataclass.

@dataclass
class Session:
    """Exact match to original Session dataclass."""
    session_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    ai_profile: Any = None  # AIProfile
    corner: str = "top-left"  # top-left, top-right, bottom-left, bottom-right
    hwnd: Optional[int] = None
    client: Optional[Any] = None  # UniversalBrowserClient or API client
    task_queue: Optional[Any] = None
    executor: Optional[Any] = None
    is_active: bool = False
    is_configured: bool = False
    iteration_count: int = 0
    current_codebase: str = ""
    codebase_path: Optional[Path] = None
    focus_history: List[str] = field(default_factory=list)
    hash_history: List[str] = field(default_factory=list)
    last_hash: str = ""
    metrics: Dict[str, Any] = field(default_factory=dict)

    def update_hash(self, code: str):
        """Update stagnation detection hash."""
        h = hashlib.md5(code.encode('utf-8')).hexdigest()
        self.hash_history.append(h)
        self.last_hash = h
        if len(self.hash_history) > 5:
            self.hash_history.pop(0)
        return h

    def is_stagnant(self, threshold: int = 3) -> bool:
        """Detect if code stopped evolving."""
        if len(self.hash_history) < threshold:
            return False
        recent = self.hash_history[-threshold:]
        return len(set(recent)) == 1  # all identical

    def save_state(self, base_dir: Path):
        """Persist session state."""
        state = {
            "session_id": self.session_id,
            "corner": self.corner,
            "iteration_count": self.iteration_count,
            "focus_history": self.focus_history,
            "last_hash": self.last_hash,
            "metrics": self.metrics,
            "timestamp": datetime.now().isoformat()
        }
        path = base_dir / f"session_{self.session_id}.json"
        path.write_text(json.dumps(state, indent=2))
        if self.codebase_path:
            self.codebase_path.write_text(self.current_codebase)

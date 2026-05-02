# From: session_manager.py:25

@dataclass
class Session:
    """One AI browser session — a window, a client, and a task queue."""
    session_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    ai_profile: AIProfile = field(default_factory=lambda: GEMINI_PROFILE)
    corner: str = "bottom-right"
    hwnd: Optional[int] = None
    client: Optional[UniversalBrowserClient] = None
    task_queue: Optional[TaskQueue] = None
    executor: Optional[TaskExecutor] = None
    is_active: bool = False
    is_configured: bool = False

    @property
    def display_name(self) -> str:
        return f"{self.ai_profile.name} ({self.corner})"

    @property
    def is_running(self) -> bool:
        return self.executor is not None and self.executor.is_running

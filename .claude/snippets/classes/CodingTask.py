# From: gemini_coder/task_manager.py:24

@dataclass
class CodingTask:
    """A coding task to be executed by an AI agent."""
    title: str = ""
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING
    output_code: Optional[str] = None
    elapsed_seconds: float = 0.0
    time_budget_seconds: float = 180.0
    progress_fraction: float = 0.0
    iterations_completed: int = 0
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    task_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    session_id: str = ""

    @property
    def is_complete(self) -> bool:
        return self.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED)

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "output_code": self.output_code,
            "elapsed_seconds": self.elapsed_seconds,
            "time_budget_seconds": self.time_budget_seconds,
            "iterations_completed": self.iterations_completed,
            "created_at": self.created_at,
            "task_id": self.task_id,
        }

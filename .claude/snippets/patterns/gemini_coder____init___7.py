# From: gemini_coder/task_manager.py:62

    def __init__(self, save_path: Optional[Path] = None) -> None:
        self._pending: list[CodingTask] = []
        self._completed: list[CodingTask] = []
        self._save_path = save_path
        self._on_change: Optional[Callable] = None

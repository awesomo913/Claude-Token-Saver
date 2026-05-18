# From: broadcast.py:190

    def __init__(self, session_manager) -> None:
        self._sm = session_manager
        self._running = False
        self._stop_event = threading.Event()
        self._threads: list[threading.Thread] = []
        self._iteration_counts: dict[str, int] = {}
        self._results: dict[str, str] = {}  # session_id -> latest actual result

        self._on_output: Optional[Callable] = None
        self._on_status: Optional[Callable] = None
        self._on_iteration: Optional[Callable] = None
        self._on_complete: Optional[Callable] = None

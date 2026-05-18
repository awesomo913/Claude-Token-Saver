# From: gemini_coder_web/ui/app_web.py:489

    def __init__(self) -> None:
        print("DEBUG: Calling super().__init__()")
        super().__init__()
        print("DEBUG: Super init completed")
        print(f"DEBUG: _content exists: {hasattr(self, '_content')}")
        if hasattr(self, '_content'):
            print(f"DEBUG: _content type: {type(self._content)}")
        # Initialize global sessions store for the new Global Create panel
        self._global_sessions = {}

        self._start_time = time.time()
        self._config_manager = ConfigManager()
        self._cfg = self._config_manager.config
        self._platform = detect_platform()

        ctk.set_appearance_mode(self._cfg.theme)
        ctk.set_default_color_theme("blue")
        self._colors = get_colors(self._cfg.theme)

        self.title(f"{__app_name__} v{__version__}")
        self.geometry(f"{self._cfg.window_width}x{self._cfg.window_height}")
        self.minsize(1000, 650)

        # ── Session manager (replaces single client) ─────────────
        # Clear any stale claimed hwnds from a previous run
        from ..universal_client import UniversalBrowserClient
        UniversalBrowserClient._claimed_hwnds.clear()

        self.session_mgr = SessionManager()

        # No default session — session cards handle creation.
        # Base class references self._gemini, so use a stub with is_configured=False.
        class _Stub:
            is_configured = False
            def cancel(self): pass
            def update_settings(self, **kw): pass
        self._gemini = _Stub()
        self._task_queue = TaskQueue()  # Empty queue until a session is selected
        self._task_executor = None
        self._expander = None  # Created when first session connects
        self._history = HistoryManager()
        # Bridge to connect GUI with backend logic
        self._bridge = GUIBridge(self.session_mgr, self._history, None)

        # Track active session for output display
        self._active_session_id = None
        self._session_outputs: dict[str, str] = {}  # session_id -> latest output

        self._current_view = "expand"
        self._last_completed_task = None
        self._session_cards: dict[str, SessionCard] = {}
        self._broadcast = BroadcastController(self.session_mgr)
        self._broadcast.set_callbacks(
            on_output=lambda sid, kind, text: self._on_session_output(sid, kind, text),
            on_status=lambda msg: self.after(0, lambda: self._bc_status.configure(text=msg)),
            on_iteration=self._on_broadcast_iteration,
        )

        self._setup_logging()
        self._build_ui()
        self._bind_shortcuts()
        self._setup_callbacks()
        self._start_clock()

        self.after(500, lambda: self._show_view("settings"))
        self.protocol("WM_DELETE_WINDOW", self._on_close)

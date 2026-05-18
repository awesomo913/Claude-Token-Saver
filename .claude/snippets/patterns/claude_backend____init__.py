# From: claude_backend/gui.py:212

    def __init__(self) -> None:
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.title("Claude Token Saver")
        self.geometry("1200x780")
        self.minsize(960, 620)
        self.configure(fg_color=C["bg"])

        self._project_path: Optional[Path] = None
        self._analysis: Optional[ProjectAnalysis] = None
        self._config = ScanConfig()
        self._mgr = ClaudeContextManager(self._config)
        self._context_queue: list[dict] = []
        self._snippets: list[CodeBlock] = []
        self._memory_files: dict[str, str] = {}
        self._busy = False
        self._session_start = time.strftime("%Y-%m-%dT%H:%M:%S")
        self._tracker = TokenTracker()
        self._session_mem = SessionMemory()
        self._ollama = OllamaManager()
        self._auto_scan_id: Optional[str] = None
        self._auto_scan_interval = 10 * 60 * 1000  # 10 minutes in ms
        self._prefs = Prefs.load()
        self._welcome_dlg: Optional[ctk.CTkToplevel] = None
        self._settings_refresh_id: Optional[str] = None

        self._build_ui()
        self._show_view("dashboard")
        self._update_token_display()

        # Show welcome on launch unless user disabled it
        if self._prefs.show_welcome_on_launch:
            self.after(400, self._open_welcome)

        # Auto-load last project if pref is set and directory still exists
        if self._prefs.last_project_path:
            last = Path(self._prefs.last_project_path)
            if last.is_dir():
                # Defer slightly so UI is fully realized before scan triggers
                self.after(200, lambda p=last: self._auto_load_project(p))

        # Watch the HTTP server's IPC pending file for incoming /improve calls.
        # When a payload appears, populate Builder and raise the window.
        self.after(1000, self._poll_pending_file)
        # v0.7.0 — single-instance bring-to-front poll. When a
        # duplicate launch detected the GUI mutex held, it wrote a
        # raise-flag file; we surface our window in response.
        self.after(1500, self._tick_single_instance_raise)

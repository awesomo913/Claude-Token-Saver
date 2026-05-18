# From: gemini_coder/ui/app.py:105

    def __init__(self) -> None:
        super().__init__()
        
        self._start_time = time.time()
        self._colors = {}
        self._views: dict = {}
        self._frames: dict = {}
        self._current_view = "main"
        
        self.title("Gemini Coder")
        self.geometry("1200x800")
        
        # Create main container
        self._content = ctk.CTkFrame(self)
        self._content.pack(fill="both", expand=True)
        
        # Initialize UI elements that subclasses will use
        self._status_bar = None
        self._task_output = None
        self._task_progress_bar = None
        self._task_progress_label = None
        self._ai_status_dot = None
        self._ai_status_label = None
        self._refresh_task_list = lambda: None

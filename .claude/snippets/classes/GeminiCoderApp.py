# From: gemini_coder/ui/app.py:102

class GeminiCoderApp(ctk.CTk):
    """Base application class for Gemini Coder desktop app."""

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

    def _setup_logging(self) -> None:
        """Setup logging for the application."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        )

    def _build_ui(self) -> None:
        """Build the main UI components."""
        pass

    def _bind_shortcuts(self) -> None:
        """Bind keyboard shortcuts."""
        self.bind("<Control-q>", lambda e: self.quit())
        self.bind("<Escape>", lambda e: self._on_escape())

    def _on_escape(self) -> None:
        """Handle escape key."""
        pass

    def _show_view(self, view_name: str) -> None:
        """Switch to a different view."""
        views = getattr(self, '_views', {}) or {}
        frames = getattr(self, '_frames', {}) or {}
        all_views = {**views, **frames}
        for name, frame in all_views.items():
            if name == view_name:
                frame.pack(fill="both", expand=True)
            else:
                frame.pack_forget()
        self._current_view = view_name

    def _start_clock(self) -> None:
        """Start the clock update."""
        self._update_clock()
        self.after(1000, self._start_clock)

    def _update_clock(self) -> None:
        """Update the clock display."""
        pass

    def _on_close(self) -> None:
        """Handle window close."""
        self.quit()

    def _toast(self, message: str, level: str = "info") -> None:
        """Show a toast notification."""
        pass

    def _show_api_key_prompt(self) -> None:
        """Show the API key prompt."""
        pass

    def _on_save_api_key(self) -> None:
        """Save the API key."""
        pass

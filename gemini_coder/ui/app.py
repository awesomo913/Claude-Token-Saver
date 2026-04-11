"""Base application class for Gemini Coder."""

import customtkinter as ctk
import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class StatusBar(ctk.CTkFrame):
    """Status bar at the bottom of the window."""

    def __init__(self, parent, colors: dict, **kwargs):
        super().__init__(parent, fg_color=colors["bg_secondary"], height=28, **kwargs)
        self._colors = colors
        
        self._status_label = ctk.CTkLabel(
            self, text="Ready", font=("Segoe UI", 11),
            text_color=colors["fg_secondary"]
        )
        self._status_label.pack(side="left", padx=10)
        
        self._clock_label = ctk.CTkLabel(
            self, text="", font=("Segoe UI", 10),
            text_color=colors["fg_muted"]
        )
        self._clock_label.pack(side="right", padx=10)
        
        self._dot = ctk.CTkLabel(
            self, text="\u25CF", font=("Segoe UI", 12),
            text_color=colors["fg_muted"]
        )
        self._dot.pack(side="right", padx=(0, 5))
        
        self.pack(fill="x", side="bottom")

    def set_status(self, message: str, level: str = "info") -> None:
        """Update the status message."""
        color_map = {
            "success": self._colors["success"],
            "warning": self._colors["warning"],
            "error": self._colors["error"],
            "info": self._colors["info"],
        }
        color = color_map.get(level, self._colors["fg_secondary"])
        self._status_label.configure(text=message, text_color=color)

    def set_dot_color(self, color: str) -> None:
        """Set the dot color."""
        self._dot.configure(text_color=color)


class ToastNotification:
    """Toast notification overlay."""

    def __init__(self, parent, colors: dict):
        self._parent = parent
        self._colors = colors
        self._label: Optional[ctk.CTkLabel] = None
        self._after_id: Optional[str] = None

    def show(self, message: str, level: str = "info") -> None:
        """Show a toast notification."""
        if self._label:
            self._label.destroy()
        if self._after_id:
            self._parent.after_cancel(self._after_id)

        color_map = {
            "success": self._colors["success"],
            "warning": self._colors["warning"],
            "error": self._colors["error"],
            "info": self._colors["info"],
        }
        color = color_map.get(level, self._colors["info"])
        bg = self._colors["bg_card"]
        
        self._label = ctk.CTkLabel(
            self._parent,
            text=message,
            font=("Segoe UI", 12),
            text_color=color,
            fg_color=bg,
            corner_radius=8,
            padx=16,
            pady=8,
        )
        
        self._label.place(relx=0.5, rely=0.95, anchor="center")
        self._label.lift()
        
        self._after_id = self._parent.after(3000, self.hide)

    def hide(self) -> None:
        """Hide the toast."""
        if self._label:
            self._label.destroy()
            self._label = None


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

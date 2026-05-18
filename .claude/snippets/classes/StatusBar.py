# From: gemini_coder/ui/app.py:11
# Status bar at the bottom of the window.

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

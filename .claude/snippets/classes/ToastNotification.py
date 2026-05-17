# From: gemini_coder/ui/app.py:54

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

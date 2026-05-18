# From: gemini_coder/ui/app.py:14

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

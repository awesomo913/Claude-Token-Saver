# From: gemini_coder/ui/app.py:57

    def __init__(self, parent, colors: dict):
        self._parent = parent
        self._colors = colors
        self._label: Optional[ctk.CTkLabel] = None
        self._after_id: Optional[str] = None

# From: claude_backend/gui.py:3369
# Toggle the Auto-Inject tutorial text.

    def _ai_show_tutorial(self) -> None:
        """Toggle the Auto-Inject tutorial text."""
        if self._ai_tutorial_visible:
            self._ai_tutorial_box.configure(height=0)
            self._ai_tutorial_visible = False
            return
        text = AI_TUTORIAL_TEXT
        self._ai_tutorial_box.configure(state="normal", height=360)
        self._ai_tutorial_box.delete("1.0", "end")
        self._ai_tutorial_box.insert("1.0", text)
        self._ai_tutorial_box.configure(state="disabled")
        self._ai_tutorial_visible = True

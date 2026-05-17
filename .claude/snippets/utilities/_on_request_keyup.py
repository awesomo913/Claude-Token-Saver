# From: claude_backend/gui.py:1127
# Debounced auto-find. Longer delay for bigger text to avoid mid-type firing.

    def _on_request_keyup(self, event=None) -> None:
        """Debounced auto-find. Longer delay for bigger text to avoid mid-type firing."""
        if self._autofind_id:
            self.after_cancel(self._autofind_id)
        text = self._get_request_text()
        delay = 1200 if len(text) > 200 else 800  # more time for big pastes
        self._autofind_id = self.after(delay, self._auto_find_dispatch)

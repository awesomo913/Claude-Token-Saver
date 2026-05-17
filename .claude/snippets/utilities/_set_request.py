# From: claude_backend/gui.py:1524
# Set the request box text from a quick-start button.

    def _set_request(self, text: str) -> None:
        """Set the request box text from a quick-start button."""
        self._request_box.delete("1.0", "end")
        self._request_box.insert("1.0", text)
        self._request_box.focus_set()
        self._request_box.mark_set("insert", "end")
        # Trigger auto-find for the quick-start text
        if self._autofind_id:
            self.after_cancel(self._autofind_id)
        self._autofind_id = self.after(300, self._auto_find_code)
        self._update_preview()

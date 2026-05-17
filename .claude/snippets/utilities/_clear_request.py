# From: claude_backend/gui.py:1514
# Clear the request box, queue, and matches.

    def _clear_request(self) -> None:
        """Clear the request box, queue, and matches."""
        self._request_box.delete("1.0", "end")
        self._context_queue.clear()
        self._smart_matches.clear()
        self._render_queue(); self._render_matches()
        self._update_preview(); self._update_token_display()
        self._auto_status.configure(text="")
        self._grab_status.configure(text="") if hasattr(self, '_grab_status') else None

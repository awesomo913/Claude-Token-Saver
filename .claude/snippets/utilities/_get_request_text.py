# From: claude_backend/gui.py:1536
# Get the user's request from the request box.

    def _get_request_text(self) -> str:
        """Get the user's request from the request box."""
        try:
            return self._request_box.get("1.0", "end").strip()
        except Exception:
            return ""

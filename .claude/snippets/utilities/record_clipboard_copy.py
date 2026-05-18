# From: claude_backend/tracker.py:196
# Record a context-to-clipboard copy.

    def record_clipboard_copy(
        self, template: str, item_count: int, tokens: int,
    ) -> None:
        """Record a context-to-clipboard copy."""
        copies = self._data.setdefault("clipboard_copies", [])
        copies.append({
            "template": template,
            "items": item_count,
            "tokens": tokens,
            "ts": _now(),
        })
        if len(copies) > 50:
            copies[:] = copies[-50:]
        self._save()

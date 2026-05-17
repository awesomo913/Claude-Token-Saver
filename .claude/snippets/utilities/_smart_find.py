# From: claude_backend/gui.py:1278
# Manual trigger: clear queue, re-search from scratch.

    def _smart_find(self) -> None:
        """Manual trigger: clear queue, re-search from scratch."""
        text = self._get_request_text()
        if not text:
            self._toast("Type what you want first", "warning"); return
        if not self._snippets:
            self._toast("Load and scan a project first", "warning"); return

        self._context_queue.clear()
        self._auto_find_dispatch()  # reuse the background dispatch

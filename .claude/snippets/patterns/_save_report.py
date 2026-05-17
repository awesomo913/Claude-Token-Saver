# From: claude_backend/gui.py:2058

    def _save_report(self) -> None:
        if not self._report_text:
            self._toast("Generate a report first", "warning"); return
        path = Path.home() / "Downloads" / f"token_saver_report_{time.strftime('%Y%m%d_%H%M%S')}.txt"
        try:
            path.write_text(self._report_text, encoding="utf-8")
            self._toast(f"Saved to {path.name}", "success")
            self._log(f"Report saved: {path}")
        except OSError as e:
            self._toast(f"Save failed: {e}", "error")

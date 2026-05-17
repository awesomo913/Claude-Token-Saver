# From: claude_backend/gui.py:3133
# Update status labels on the main thread from probe results.

    def _apply_backend_status(self, backend_up: bool, overlay_up: bool,
                              port: int, show_overlay: bool,
                              error: Optional[str]) -> None:
        """Update status labels on the main thread from probe results."""
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return

        if hasattr(self, "_bk_status_lbl"):
            if error is not None:
                self._bk_status_lbl.configure(
                    text=f"check failed: {error}", text_color=C["err"],
                )
            elif backend_up:
                self._bk_status_lbl.configure(
                    text=f"RUNNING on 127.0.0.1:{port}", text_color=C["ok"],
                )
            else:
                self._bk_status_lbl.configure(
                    text="NOT RUNNING (tray needs to start it)",
                    text_color=C["warn"],
                )

        if hasattr(self, "_ov_status_lbl"):
            if error is not None:
                self._ov_status_lbl.configure(
                    text=f"check failed: {error}", text_color=C["err"],
                )
            elif overlay_up:
                self._ov_status_lbl.configure(
                    text="Overlay process running", text_color=C["ok"],
                )
            elif show_overlay:
                self._ov_status_lbl.configure(
                    text="Toggle ON but process not running",
                    text_color=C["warn"],
                )
            else:
                self._ov_status_lbl.configure(
                    text="Disabled", text_color=C["fg3"],
                )

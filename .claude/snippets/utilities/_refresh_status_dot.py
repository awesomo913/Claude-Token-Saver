# From: claude_backend/gui.py:485
# Poll HTTP backend health; recolor the status-bar dot accordingly.

    def _refresh_status_dot(self) -> None:
        """Poll HTTP backend health; recolor the status-bar dot accordingly."""
        try:
            from .http_server import is_backend_alive
            from .prefs import Prefs
            port = Prefs.load().http_port
            up = is_backend_alive(port)
            self._st_dot.configure(text_color=C["ok"] if up else C["err"])
        except Exception as e:
            logger.debug("status-dot poll failed: %s", e)
            try:
                self._st_dot.configure(text_color=C["fg3"])
            except Exception:
                pass
        # Re-arm every 5s. Cheap call, no big deal if it overlaps with
        # window teardown — Tk after() is canceled on destroy.
        try:
            self.after(5000, self._refresh_status_dot)
        except Exception:
            pass

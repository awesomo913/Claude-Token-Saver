# From: claude_backend/overlay.py:217
# Set window translucency; clamped + cached so we don't pound

    def _set_alpha(self, alpha: float) -> None:
        """Set window translucency; clamped + cached so we don't pound
        Tk with redundant updates."""
        a = max(0.05, min(1.0, float(alpha)))
        if abs(a - self._current_alpha) < 0.01:
            return
        try:
            self.attributes("-alpha", a)
            self._current_alpha = a
        except Exception:  # noqa: BLE001
            pass

# From: claude_backend/overlay.py:98

    def __init__(self, parent: ctk.CTk) -> None:
        super().__init__(parent)
        self._parent = parent
        self._prefs = Prefs.load()
        self._drag_data = {"x": 0, "y": 0, "moved": False}
        self._locked = False
        # Fade state: ms-since-epoch of last time cursor was near.
        self._last_proximity_ms = 0
        self._current_alpha = _FADE_ACTIVE_ALPHA
        self._fade_job: str | None = None
        # Most recent foreground HWND that's NOT us — captured on every
        # proximity poll tick so a click can restore focus to the
        # window the user was actually typing in (e.g. Chrome) before
        # firing the Ctrl+A+Ctrl+C macro. Without this the macro
        # would hit our own borderless overlay window.
        self._last_external_hwnd: int = 0

        self.title("Token Saver Overlay")
        self.overrideredirect(True)  # no titlebar / borders
        self.attributes("-topmost", True)
        self.geometry(f"{_OVERLAY_W}x{_OVERLAY_H}")
        self.configure(fg_color=_C["card"])

        # Restore position; default = top-right of screen
        x, y = self._restore_position()
        self.geometry(f"{_OVERLAY_W}x{_OVERLAY_H}+{x}+{y}")

        self._build()

        # Allow drag-to-move on the frame, double-click to lock
        self.bind("<Button-1>", self._on_drag_start)
        self.bind("<B1-Motion>", self._on_drag_motion)
        self.bind("<ButtonRelease-1>", self._on_drag_end)
        self.bind("<Double-Button-1>", self._toggle_lock)

        # Start the proximity-fade poller after the window has rendered.
        # We mark proximity initially so the user sees the button at full
        # opacity when it first appears — fading in cold would be ugly.
        self._last_proximity_ms = int(time.time() * 1000)
        self.after(_FADE_POLL_MS, self._poll_proximity)

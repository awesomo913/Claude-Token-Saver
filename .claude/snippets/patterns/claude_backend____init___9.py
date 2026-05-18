# From: claude_backend/welcome.py:118

    def __init__(self, parent: ctk.CTk, prefs: Prefs,
                 on_install_callback: Optional[Callable[[], None]] = None) -> None:
        super().__init__(parent)
        self._prefs = prefs
        self._on_install = on_install_callback

        self.title(WELCOME_TITLE)
        self.geometry("780x680")
        self.minsize(680, 560)
        self.configure(fg_color=_C["bg"])
        self.transient(parent)

        # Center on parent
        self.after(50, self._center_on_parent)

        self._build()
        self._refresh_status()

        # Bump seen count immediately
        self._prefs.welcome_seen_count += 1
        self._prefs.save()

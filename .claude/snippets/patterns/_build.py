# From: claude_backend/overlay.py:161

    def _build(self) -> None:
        # Outer Toplevel acts as the "border": fg_color is the border color.
        # Inner frame holds the button and is shrunk 2px on each side via
        # pack padding so the purple shows around the edges. (CustomTkinter
        # rejects negative width/height in .place(), so use pack instead.)
        border_color = _C["purple"]
        self.configure(fg_color=border_color)
        inner = ctk.CTkFrame(self, fg_color=_C["card"], corner_radius=6)
        inner.pack(fill="both", expand=True, padx=2, pady=2)

        btn = ctk.CTkButton(
            inner,
            text="🪄 Improve",
            font=("Segoe UI", 12, "bold"),
            fg_color=_C["purple"],
            hover_color="#6d2d8e",
            text_color="#ffffff",
            corner_radius=4,
            height=28,
            command=self._on_click,
        )
        btn.pack(fill="both", expand=True, padx=4, pady=4)
        # Drag bindings on button too (else clicking the button would always fire)
        btn.bind("<Button-1>", self._on_drag_start, add="+")
        btn.bind("<B1-Motion>", self._on_drag_motion, add="+")
        btn.bind("<ButtonRelease-1>", self._on_drag_end, add="+")
        btn.bind("<Double-Button-1>", self._toggle_lock, add="+")

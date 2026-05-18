# From: claude_backend/welcome.py:155

    def _build(self) -> None:
        scroll = ctk.CTkScrollableFrame(self, fg_color=_C["bg"])
        scroll.pack(fill="both", expand=True, padx=18, pady=(18, 0))

        # Header
        ctk.CTkLabel(scroll, text=WELCOME_TITLE, font=(_F, 22, "bold"),
                     text_color=_C["accent"]).pack(anchor="w", pady=(0, 6))
        ctk.CTkLabel(scroll, text=WELCOME_INTRO, font=(_F, 12),
                     text_color=_C["fg2"], wraplength=720, justify="left"
                     ).pack(anchor="w", pady=(0, 16))

        # Status card — Auto-Inject install state with quick action
        self._status_card = ctk.CTkFrame(scroll, fg_color=_C["card"], corner_radius=8,
                                         border_width=2, border_color=_C["ok"])
        self._status_card.pack(fill="x", pady=(0, 16))
        self._status_label = ctk.CTkLabel(
            self._status_card, text="Checking Auto-Inject...",
            font=(_F, 13, "bold"), text_color=_C["fg"],
        )
        self._status_label.pack(anchor="w", padx=14, pady=(12, 4))
        self._status_detail = ctk.CTkLabel(
            self._status_card, text="", font=(_F, 11),
            text_color=_C["fg2"], wraplength=700, justify="left",
        )
        self._status_detail.pack(anchor="w", padx=14, pady=(0, 8))
        self._status_btn = ctk.CTkButton(
            self._status_card, text="Install Auto-Inject", width=180, height=32,
            font=(_F, 12, "bold"), fg_color=_C["ok"],
            command=self._do_install,
        )
        self._status_btn.pack(anchor="w", padx=14, pady=(0, 12))

        # What it does
        self._section(scroll, "What it does")
        for title, body in WHAT_IT_DOES:
            self._bullet(scroll, title, body)

        # Permissions
        self._section(scroll, "Permissions used")
        ctk.CTkLabel(scroll,
                     text="Full transparency on what this tool reads and writes:",
                     font=(_F, 11), text_color=_C["fg3"], wraplength=720, justify="left",
                     ).pack(anchor="w", pady=(0, 8))
        for title, body in PERMISSIONS:
            self._bullet(scroll, title, body)

        # Quick start
        self._section(scroll, "Quick start")
        for step in QUICK_START:
            ctk.CTkLabel(scroll, text=step, font=(_F, 11),
                         text_color=_C["fg2"], wraplength=720, justify="left",
                         ).pack(anchor="w", padx=14, pady=2)

        # Pro tip
        tip_card = ctk.CTkFrame(scroll, fg_color=_C["card"], corner_radius=8,
                                border_width=1, border_color=_C["purple"])
        tip_card.pack(fill="x", pady=(16, 8))
        ctk.CTkLabel(tip_card, text="Pro tip", font=(_F, 12, "bold"),
                     text_color=_C["purple"]).pack(anchor="w", padx=14, pady=(10, 2))
        ctk.CTkLabel(tip_card, text=PRO_TIP, font=(_F, 11),
                     text_color=_C["fg2"], wraplength=700, justify="left",
                     ).pack(anchor="w", padx=14, pady=(0, 12))

        # Footer — fixed below scroll area
        footer = ctk.CTkFrame(self, fg_color=_C["bg2"], corner_radius=0, height=64)
        footer.pack(side="bottom", fill="x")
        footer.pack_propagate(False)

        self._dont_show = ctk.CTkCheckBox(
            footer, text="Don't show this on launch (always available via Help button)",
            font=(_F, 11), text_color=_C["fg2"],
            command=self._toggle_dont_show,
        )
        self._dont_show.pack(side="left", padx=18, pady=18)
        if not self._prefs.show_welcome_on_launch:
            self._dont_show.select()

        ctk.CTkButton(
            footer, text="Got it — close", width=140, height=32,
            font=(_F, 12, "bold"), fg_color=_C["accent"],
            command=self._dismiss,
        ).pack(side="right", padx=18, pady=16)

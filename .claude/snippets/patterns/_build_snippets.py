# From: claude_backend/gui.py:1713

    def _build_snippets(self) -> None:
        fr = ctk.CTkFrame(self._content, fg_color=C["bg"])
        self._views["snippets"] = fr
        ctk.CTkLabel(fr, text="Snippets", font=(F, 20, "bold"), text_color=C["fg"]).pack(padx=20, pady=(16, 2), anchor="w")
        ctk.CTkLabel(fr, text="Browse by area or search. Click + Context to add to your prompt.",
                     font=(F, 11), text_color=C["fg3"]).pack(padx=20, anchor="w", pady=(0, 8))

        srow = ctk.CTkFrame(fr, fg_color="transparent"); srow.pack(fill="x", padx=20, pady=(0, 4))
        self._s_search = ctk.CTkEntry(srow, placeholder_text="Search: type anything... (e.g. 'browser stuff' or 'save files')",
                                      font=(F, 12), fg_color=C["input"], border_color=C["border"], height=34)
        self._s_search.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self._s_search.bind("<KeyRelease>", lambda e: self._filter_snips())

        # Domain tabs — built dynamically after scan
        self._s_tab_frame = ctk.CTkFrame(fr, fg_color="transparent")
        self._s_tab_frame.pack(fill="x", padx=20, pady=(0, 6))
        self._s_domain_btns: list[ctk.CTkButton] = []
        self._s_active_domain = "All"

        sp = ctk.CTkFrame(fr, fg_color="transparent"); sp.pack(fill="both", expand=True, padx=20, pady=(0, 16))
        self._s_list = ctk.CTkScrollableFrame(sp, fg_color=C["bg2"], corner_radius=8,
                                              border_width=1, border_color=C["border"], width=400)
        self._s_list.pack(side="left", fill="both", expand=False, padx=(0, 8))
        self._s_cards: list[ctk.CTkFrame] = []
        self._s_prev = ctk.CTkTextbox(sp, font=(M, 12), fg_color=C["card"], border_color=C["border"],
                                      border_width=1, text_color="#d4d4d4", state="disabled", wrap="none")
        self._s_prev.pack(side="left", fill="both", expand=True)

# From: claude_backend/gui.py:540

    def _build_dashboard(self) -> None:
        fr = ctk.CTkScrollableFrame(self._content, fg_color=C["bg"])
        self._views["dashboard"] = fr

        ctk.CTkLabel(fr, text="Dashboard", font=(F, 20, "bold"),
                     text_color=C["fg"]).pack(padx=20, pady=(16, 4), anchor="w")
        ctk.CTkLabel(fr, text="Step 1: Load a project folder, then Bootstrap to generate context files.",
                     font=(F, 11), text_color=C["fg3"]).pack(padx=20, anchor="w", pady=(0, 8))

        # Project selector
        pcard = ctk.CTkFrame(fr, fg_color=C["card"], corner_radius=8, border_width=1, border_color=C["border"])
        pcard.pack(fill="x", padx=20, pady=(0, 8))
        prow = ctk.CTkFrame(pcard, fg_color="transparent"); prow.pack(fill="x", padx=12, pady=10)
        ctk.CTkLabel(prow, text="Project:", font=(F, 12), text_color=C["fg2"]).pack(side="left", padx=(0, 8))
        self._d_path = ctk.CTkEntry(prow, placeholder_text="Select project folder...",
                                    font=(F, 12), fg_color=C["input"], border_color=C["border"], height=34)
        self._d_path.pack(side="left", fill="x", expand=True, padx=(0, 6))
        ctk.CTkButton(prow, text="Browse", width=80, height=34, font=(F, 11),
                      fg_color=C["accent"], command=lambda: self._pick_folder(self._d_path)).pack(side="left", padx=(0, 6))
        ctk.CTkButton(prow, text="Load", width=70, height=34, font=(F, 11, "bold"),
                      fg_color=C["ok"], command=self._on_load).pack(side="left")

        # Actions
        arow = ctk.CTkFrame(fr, fg_color="transparent"); arow.pack(fill="x", padx=20, pady=(0, 8))
        for txt, col, cmd in [("Bootstrap (First Time)", C["accent"], self._on_bootstrap),
                              ("Prep (Update)", C["purple"], self._on_prep),
                              ("Scan Only", C["bg2"], self._on_scan),
                              ("Clean", C["err"], self._on_clean)]:
            ctk.CTkButton(arow, text=txt, font=(F, 11, "bold"), fg_color=col,
                          height=34, width=160, command=cmd).pack(side="left", padx=(0, 6))

        # Token savings
        srow = ctk.CTkFrame(fr, fg_color="transparent"); srow.pack(fill="x", padx=20, pady=(0, 6))
        self._sav: dict[str, ctk.CTkLabel] = {}
        for lbl, clr, w in [("All-Time Saved", C["ok"], 160), ("Project Saved", C["accent"], 150),
                            ("This Session", C["purple"], 140), ("Copies", C["warn"], 100)]:
            cd = ctk.CTkFrame(srow, fg_color=C["card"], corner_radius=8, border_width=1,
                              border_color=clr, width=w, height=68)
            cd.pack(side="left", padx=(0, 6), pady=2); cd.pack_propagate(False)
            ctk.CTkLabel(cd, text=lbl, font=(F, 9), text_color=clr).pack(pady=(8, 0))
            v = ctk.CTkLabel(cd, text="0", font=(F, 18, "bold"), text_color=C["fg"])
            v.pack(pady=(0, 6)); self._sav[lbl] = v

        # Stats
        srow2 = ctk.CTkFrame(fr, fg_color="transparent"); srow2.pack(fill="x", padx=20, pady=(0, 6))
        self._stats: dict[str, ctk.CTkLabel] = {}
        for lbl in ["Files", "Modules", "Blocks", "Snippets", "Memory"]:
            cd = ctk.CTkFrame(srow2, fg_color=C["card"], corner_radius=8, border_width=1,
                              border_color=C["border"], width=130, height=62)
            cd.pack(side="left", padx=(0, 6), pady=2); cd.pack_propagate(False)
            ctk.CTkLabel(cd, text=lbl, font=(F, 9), text_color=C["fg3"]).pack(pady=(6, 0))
            v = ctk.CTkLabel(cd, text="--", font=(F, 18, "bold"), text_color=C["fg"])
            v.pack(pady=(0, 4)); self._stats[lbl] = v

        # Conventions
        self._conv_fr = ctk.CTkFrame(fr, fg_color=C["card"], corner_radius=8, border_width=1, border_color=C["border"])
        self._conv_fr.pack(fill="x", padx=20, pady=(0, 6))
        ctk.CTkLabel(self._conv_fr, text="Detected Conventions", font=(F, 12, "bold"),
                     text_color=C["fg"]).pack(padx=12, pady=(8, 4), anchor="w")
        self._conv_badges = ctk.CTkFrame(self._conv_fr, fg_color="transparent")
        self._conv_badges.pack(fill="x", padx=12, pady=(0, 8))
        self._conv_lbls: list[ctk.CTkLabel] = []

        # Recent activity
        self._act_fr = ctk.CTkFrame(fr, fg_color=C["card"], corner_radius=8, border_width=1, border_color=C["border"])
        self._act_fr.pack(fill="x", padx=20, pady=(0, 6))
        ctk.CTkLabel(self._act_fr, text="Recent Context Activity", font=(F, 12, "bold"),
                     text_color=C["fg"]).pack(padx=12, pady=(8, 4), anchor="w")
        self._act_items = ctk.CTkFrame(self._act_fr, fg_color="transparent")
        self._act_items.pack(fill="x", padx=12, pady=(0, 8))
        self._act_lbls: list[ctk.CTkLabel] = []

        # Log
        ctk.CTkLabel(fr, text="Activity Log", font=(F, 12, "bold"),
                     text_color=C["fg"]).pack(padx=20, anchor="w")
        self._log_box = ctk.CTkTextbox(fr, font=(M, 10), fg_color=C["card"], border_color=C["border"],
                                       border_width=1, text_color=C["fg2"], state="disabled", height=120)
        self._log_box.pack(fill="x", padx=20, pady=(4, 16))

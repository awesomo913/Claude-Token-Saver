# From: claude_backend/gui.py:276

    def _build_ui(self) -> None:
        # Sidebar
        sb = ctk.CTkFrame(self, width=180, fg_color=C["sidebar"], corner_radius=0)
        sb.pack(side="left", fill="y"); sb.pack_propagate(False)
        ctk.CTkLabel(sb, text="Token Saver", font=(F, 16, "bold"),
                     text_color=C["accent"]).pack(pady=(18, 24), padx=12, anchor="w")

        self._nav_btns: dict[str, ctk.CTkButton] = {}
        for key, label in [("dashboard", "1  Dashboard"), ("builder", "2  Context Builder"),
                           ("snippets", "3  Snippets"), ("memory", "4  Memory"),
                           ("report", "5  Analysis Report"),
                           ("settings", "6  Settings")]:
            b = ctk.CTkButton(sb, text=f"  {label}", anchor="w", font=(F, 13), height=38,
                              fg_color="transparent", hover_color=C["side_act"],
                              text_color=C["fg2"], corner_radius=6,
                              command=lambda k=key: self._show_view(k))
            b.pack(fill="x", padx=8, pady=2); self._nav_btns[key] = b

        # Help button — always visible, always available
        help_btn = ctk.CTkButton(
            sb, text="  ?  Help / Welcome", anchor="w", font=(F, 12, "bold"),
            height=36, fg_color="transparent", hover_color=C["side_act"],
            text_color=C["accent"], corner_radius=6,
            command=self._open_welcome,
        )
        help_btn.pack(fill="x", padx=8, pady=(20, 4), side="bottom")

        ctk.CTkLabel(sb, text="v4.5", font=(F, 9), text_color=C["fg3"]).pack(side="bottom", pady=8)

        self._content = ctk.CTkFrame(self, fg_color=C["bg"], corner_radius=0)
        self._content.pack(side="left", fill="both", expand=True)

        bar = ctk.CTkFrame(
            self, height=36, fg_color=C["bar_bg"], corner_radius=0,
            border_width=1, border_color=C["border_soft"],
        )
        bar.pack(side="bottom", fill="x"); bar.pack_propagate(False)
        # Backend state dot — green = HTTP up, red = down. Poll every 5s.
        self._st_dot = ctk.CTkLabel(
            bar, text="●", font=(F, 14, "bold"), text_color=C["fg3"],
        )
        self._st_dot.pack(side="left", padx=(12, 4))
        self._st_label = ctk.CTkLabel(bar, text="Ready", font=(F, 10), text_color=C["fg2"])
        self._st_label.pack(side="left", padx=4)
        self._st_proj = ctk.CTkLabel(bar, text="No project loaded", font=(F, 10), text_color=C["fg3"])
        self._st_proj.pack(side="right", padx=12)
        self._refresh_status_dot()  # schedule self-renewing poll

        self._toast_lbl: Optional[ctk.CTkLabel] = None
        self._toast_id: Optional[str] = None
        self._toast_anim_ids: list[str] = []

        self._views: dict[str, ctk.CTkFrame] = {}
        self._build_dashboard()
        self._build_builder()
        self._build_snippets()
        self._build_memory()
        self._build_report()
        self._build_settings()

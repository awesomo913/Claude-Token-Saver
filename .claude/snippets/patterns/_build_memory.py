# From: claude_backend/gui.py:1816

    def _build_memory(self) -> None:
        fr = ctk.CTkFrame(self._content, fg_color=C["bg"])
        self._views["memory"] = fr
        ctk.CTkLabel(fr, text="Memory Files", font=(F, 20, "bold"), text_color=C["fg"]).pack(padx=20, pady=(16, 2), anchor="w")
        ctk.CTkLabel(fr, text="These files are auto-loaded by Claude Code for persistent context across sessions.",
                     font=(F, 11), text_color=C["fg3"]).pack(padx=20, anchor="w", pady=(0, 8))
        sp = ctk.CTkFrame(fr, fg_color="transparent"); sp.pack(fill="both", expand=True, padx=20, pady=(0, 16))
        self._m_list = ctk.CTkScrollableFrame(sp, fg_color=C["bg2"], corner_radius=8,
                                              border_width=1, border_color=C["border"], width=280)
        self._m_list.pack(side="left", fill="both", padx=(0, 8))
        self._m_cards: list[ctk.CTkFrame] = []
        self._m_prev = ctk.CTkTextbox(sp, font=(M, 12), fg_color=C["card"], border_color=C["border"],
                                      border_width=1, text_color="#d4d4d4", state="disabled")
        self._m_prev.pack(side="left", fill="both", expand=True)

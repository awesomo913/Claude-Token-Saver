# From: claude_backend/gui.py:1911

    def _build_report(self) -> None:
        fr = ctk.CTkScrollableFrame(self._content, fg_color=C["bg"])
        self._views["report"] = fr

        ctk.CTkLabel(fr, text="Analysis Report", font=(F, 20, "bold"),
                     text_color=C["fg"]).pack(padx=20, pady=(16, 2), anchor="w")
        ctk.CTkLabel(fr, text="Shareable token savings analysis. No personal data included.",
                     font=(F, 11), text_color=C["fg3"]).pack(padx=20, anchor="w", pady=(0, 8))

        # Action buttons
        br = ctk.CTkFrame(fr, fg_color="transparent"); br.pack(fill="x", padx=20, pady=(0, 8))
        ctk.CTkButton(br, text="Generate Report", font=(F, 12, "bold"), fg_color=C["accent"],
                      height=36, width=160, command=self._gen_report).pack(side="left", padx=(0, 8))
        ctk.CTkButton(br, text="Copy Report", font=(F, 12), fg_color=C["purple"],
                      height=36, width=130, command=self._copy_report).pack(side="left", padx=(0, 8))
        ctk.CTkButton(br, text="Save as .txt", font=(F, 12), fg_color=C["bg2"],
                      height=36, width=110, command=self._save_report).pack(side="left")

        self._report_box = ctk.CTkTextbox(fr, font=(M, 11), fg_color=C["card"],
                                          border_color=C["border"], border_width=1,
                                          text_color="#d4d4d4", state="disabled")
        self._report_box.pack(fill="both", expand=True, padx=20, pady=(0, 16))
        self._report_text = ""

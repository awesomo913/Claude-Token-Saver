# From: claude_backend/gui.py:1831

    def _load_memory(self) -> None:
        if not self._project_path: return
        self._memory_files.clear()
        md = self._project_path / ".claude" / "memory"
        if md.is_dir():
            for f in sorted(md.iterdir()):
                if f.is_file() and f.suffix == ".md":
                    try: self._memory_files[f.name] = f.read_text(encoding="utf-8", errors="replace")
                    except OSError: pass
        for c in self._m_cards: c.destroy()
        self._m_cards.clear()
        if not self._memory_files:
            l = ctk.CTkLabel(self._m_list, text="No memory files yet.\nRun Bootstrap on the Dashboard first.",
                             font=(F, 11), text_color=C["fg3"], wraplength=240)
            l.pack(padx=8, pady=20); self._m_cards.append(l); return
        for fn, cnt in self._memory_files.items():
            cd = ctk.CTkFrame(self._m_list, fg_color=C["card"], corner_radius=6, border_width=1, border_color=C["border"])
            cd.pack(fill="x", padx=4, pady=3); self._m_cards.append(cd)
            ctk.CTkLabel(cd, text=fn.replace("_", " ").replace(".md", "").title(),
                         font=(F, 12, "bold"), text_color=C["fg"]).pack(padx=8, pady=(6, 2), anchor="w")
            ctk.CTkLabel(cd, text=f"{cnt.count(chr(10))} lines", font=(F, 9), text_color=C["fg3"]).pack(padx=8, anchor="w")
            br = ctk.CTkFrame(cd, fg_color="transparent"); br.pack(fill="x", padx=8, pady=(2, 6))
            ctk.CTkButton(br, text="Copy", width=55, height=24, font=(F, 10), fg_color=C["accent"],
                          command=lambda c=cnt: self._copy_clip(c)).pack(side="left", padx=(0, 4))
            ctk.CTkButton(br, text="+ Context", width=80, height=24, font=(F, 10), fg_color=C["purple"],
                          command=lambda f=fn, c=cnt: self._add_to_context(f, "memory", c)).pack(side="left")
            cd.bind("<Button-1>", lambda e, c=cnt: self._prev_mem(c))
            for ch in cd.winfo_children(): ch.bind("<Button-1>", lambda e, c=cnt: self._prev_mem(c))

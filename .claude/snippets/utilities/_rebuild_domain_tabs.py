# From: claude_backend/gui.py:1741
# Rebuild domain filter tabs after scanning.

    def _rebuild_domain_tabs(self) -> None:
        """Rebuild domain filter tabs after scanning."""
        for b in self._s_domain_btns: b.destroy()
        self._s_domain_btns.clear()
        domains = ["All"] + get_all_domains(self._snippets)
        for dom in domains:
            clr = C["accent"] if dom == "All" else get_domain_color(dom)
            active = dom == self._s_active_domain
            btn = ctk.CTkButton(
                self._s_tab_frame, text=dom, width=0, height=26, font=(F, 10),
                fg_color=clr if active else C["bg2"],
                hover_color=C["hover"], corner_radius=4,
                text_color=C["fg"] if active else C["fg2"],
                command=lambda d=dom: self._set_domain(d),
            )
            btn.pack(side="left", padx=2, pady=2)
            self._s_domain_btns.append(btn)

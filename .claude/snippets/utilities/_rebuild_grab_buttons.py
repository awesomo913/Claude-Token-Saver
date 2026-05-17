# From: claude_backend/gui.py:1432
# Build Quick Grab buttons from detected domains.

    def _rebuild_grab_buttons(self) -> None:
        """Build Quick Grab buttons from detected domains."""
        for b in self._grab_btns: b.destroy()
        self._grab_btns.clear()
        if hasattr(self, '_grab_placeholder') and self._grab_placeholder:
            self._grab_placeholder.destroy()
            self._grab_placeholder = None

        if not self._snippets:
            self._grab_placeholder = ctk.CTkLabel(
                self._grab_row1, text="Load a project on Dashboard first, then areas appear here",
                font=(F, 10), text_color=C["fg3"])
            self._grab_placeholder.pack(anchor="w", pady=4)
            return

        domains = get_all_domains(self._snippets)
        # Skip "Other" — it's a junk drawer, not useful for Quick Grab
        domains = [d for d in domains if d != "Other"]
        if not domains: return

        self._grab_status.configure(text=f"{len(domains)} areas found")

        for i, dom in enumerate(domains):
            count = sum(1 for s in self._snippets if get_domain(s.file_path) == dom)
            if count < 2:
                continue  # Skip domains with only 1 snippet
            clr = get_domain_color(dom)
            parent = self._grab_row1 if i < 6 else self._grab_row2
            btn = ctk.CTkButton(
                parent, text=f"{dom} ({count})", width=0, height=30,
                font=(F, 10, "bold"), fg_color=clr, hover_color=C["hover"],
                corner_radius=6,
                command=lambda d=dom: self._quick_grab(d),
            )
            btn.pack(side="left", padx=3, pady=2)
            self._grab_btns.append(btn)

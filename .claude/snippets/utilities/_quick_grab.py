# From: claude_backend/gui.py:1469
# Add the top snippets from a domain to the context queue.

    def _quick_grab(self, domain: str) -> None:
        """Add the top snippets from a domain to the context queue.

        Picks the most useful ones: documented first, focused functions over huge classes.
        """
        if not self._snippets:
            self._toast("Load and scan a project first", "warning"); return

        domain_blocks = [b for b in self._snippets if get_domain(b.file_path) == domain]
        if not domain_blocks:
            self._toast(f"No code found in {domain}", "warning"); return

        # Score and sort: documented + short = most useful for beginners
        def usefulness(b):
            score = 0
            if b.docstring and len(b.docstring) > 10: score += 100
            if b.kind in ("function", "async_function"): score += 50
            if b.kind == "class": score += 30
            lines = b.end_line - b.start_line
            if lines < 30: score += 40   # prefer focused code
            elif lines < 60: score += 20
            return -score  # negative for ascending sort
        domain_blocks.sort(key=usefulness)

        added = 0
        names_added = []
        for b in domain_blocks[:4]:
            if not any(q["name"] == b.name for q in self._context_queue):
                self._context_queue.append({"name": b.name, "source": b.file_path, "content": b.source})
                names_added.append(b.name)
                added += 1

        if added:
            self._render_queue(); self._render_matches()
            self._update_suggestions(); self._update_recent()
            self._update_preview(); self._update_token_display()
            # Show what was grabbed
            short_names = ", ".join(names_added[:3])
            if len(names_added) > 3:
                short_names += f" +{len(names_added) - 3} more"
            self._grab_status.configure(text=f"Grabbed: {short_names}")
            self._toast(f"Added {added} {domain} snippets to your prompt", "success")
        else:
            self._toast(f"All {domain} code already in your prompt", "info")

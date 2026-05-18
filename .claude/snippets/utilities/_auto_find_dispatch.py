# From: claude_backend/gui.py:1135
# Dispatch auto-find on background thread so GUI never blocks.

    def _auto_find_dispatch(self) -> None:
        """Dispatch auto-find on background thread so GUI never blocks.

        Beginner-friendly: grabs more context than asked for.
        If user mentions one function, also grabs related functions from the same file.
        """
        text = self._get_request_text()
        if not text or len(text) < 5 or not self._snippets:
            self._update_preview(); return

        is_large = len(text) > 150 or len(text.split()) > 25
        snippets_ref = self._snippets

        if is_large:
            self._auto_status.configure(text="Breaking down your request...")
        else:
            self._auto_status.configure(text="Finding relevant code...")

        def do():
            if is_large:
                results = self._breakdown_large_request(text, snippets_ref)
            else:
                # Lower threshold for beginners — grab more, not less
                results = smart_search(snippets_ref, text, max_results=5, min_score=4.0)

            if not results:
                return []

            # ── Beginner boost: also grab "neighbors" from the same files ──
            # If we found send_message from browser_actions.py, also grab
            # other key functions from browser_actions.py that the user
            # probably needs but didn't know to ask for.
            found_files = {b.file_path for _, b in results}
            found_names = {b.name for _, b in results}
            neighbors: list[tuple[float, CodeBlock]] = []
            for b in snippets_ref:
                if b.name in found_names:
                    continue
                if b.file_path in found_files and b.docstring:
                    # Same file + has docstring = likely important related code
                    neighbors.append((2.0, b))  # low score so they rank below direct matches

            # Merge: direct matches first, then neighbors, cap at 10 total
            combined = list(results[:4]) + neighbors[:2]
            return combined

        def done(results):
            if not results:
                self._auto_status.configure(text="No matches found. Try Quick Grab or Snippets tab.")
                self._update_preview(); return

            MAX_QUEUE = 15
            added = 0
            for score, block in results[:6]:
                if len(self._context_queue) >= MAX_QUEUE:
                    break
                if not any(q["name"] == block.name for q in self._context_queue):
                    self._context_queue.append({
                        "name": block.name, "source": block.file_path, "content": block.source
                    })
                    added += 1
            if added:
                self._smart_matches = [b for _, b in results[:6]]
                self._render_queue(); self._render_matches()
                self._update_suggestions(); self._update_recent()
                self._update_token_display()
                files = len({b.file_path for _, b in results[:6]})
                self._auto_status.configure(text=f"Found {added} snippets from {files} files")
                if len(self._context_queue) >= MAX_QUEUE:
                    self._auto_status.configure(text=f"{added} added (queue full at {MAX_QUEUE})")
            else:
                self._auto_status.configure(text="")
            self._compress_if_needed()
            self._update_preview()

        self._run_async(do, done)

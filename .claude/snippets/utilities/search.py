# From: claude_backend/search.py:541
# Search using the pre-built index. Fast even on 10K+ blocks.

    def search(self, query: str, max_results: int = 15, min_score: float = 3.0
               ) -> list[tuple[float, CodeBlock]]:
        """Search using the pre-built index. Fast even on 10K+ blocks."""
        if not query.strip():
            return []

        raw = re.sub(r"[^a-z0-9_ ]", " ", query.lower().strip())
        raw_words = [w for w in raw.split() if len(w) > 1]
        expanded = _expand_query(query)

        # Candidate selection: only score blocks that match at least one term
        candidates: set[int] = set()
        all_terms = set(raw_words) | set(expanded)
        for term in all_terms:
            candidates.update(self._name_index.get(term, set()))
            candidates.update(self._doc_index.get(term, set()))
            candidates.update(self._path_index.get(term, set()))
            candidates.update(self._kind_index.get(term, set()))
            # Also check stems
            st = _stem(term)
            candidates.update(self._name_index.get(st, set()))
            candidates.update(self._doc_index.get(st, set()))
            # Prefix match for fuzzy
            if len(term) >= 3:
                candidates.update(self._name_index.get(term[:3], set()))

        # Score only candidates (not all blocks)
        results: list[tuple[float, CodeBlock]] = []
        for idx in candidates:
            block = self._snippets[idx]
            sc = score_block(block, expanded, raw_words)
            if sc < min_score:
                continue
            # Penalize very large blocks — they waste tokens. Skip for
            # classes: they're inherently bigger (TokenTracker=83L, etc.),
            # the injection-time token budget already caps oversize, and
            # the penalty was double-counting against semantically-dense
            # class hits.
            if block.kind != "class":
                lines = block.end_line - block.start_line + 1
                if lines > 100:
                    sc *= 0.5
                elif lines > 50:
                    sc *= 0.75
            results.append((sc, block))

        # Deduplicate: same function from duplicate file paths (e.g. cdp_client.py vs gemini_coder_web/cdp_client.py)
        seen: dict[str, int] = {}  # "name:source_prefix" -> index in deduped
        deduped: list[tuple[float, CodeBlock]] = []
        for sc, block in sorted(results, key=lambda x: -x[0]):
            key = f"{block.name}:{block.source[:200]}"
            if key in seen:
                # Keep the one with shorter path (less nested = more canonical)
                existing_idx = seen[key]
                if len(block.file_path) < len(deduped[existing_idx][1].file_path):
                    deduped[existing_idx] = (sc, block)
            else:
                seen[key] = len(deduped)
                deduped.append((sc, block))

        return deduped[:max_results]

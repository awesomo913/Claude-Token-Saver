# From: claude_backend/search.py:495
# Pre-computed inverted index for fast searching over large snippet sets.

class SearchIndex:
    """Pre-computed inverted index for fast searching over large snippet sets.

    Build once after scanning, then run many queries against it.
    Avoids running SequenceMatcher on every block for every query.
    """

    def __init__(self, snippets: list[CodeBlock]) -> None:
        self._snippets = snippets
        # Inverted index: word -> set of block indices
        self._name_index: dict[str, set[int]] = {}
        self._doc_index: dict[str, set[int]] = {}
        self._path_index: dict[str, set[int]] = {}
        self._kind_index: dict[str, set[int]] = {}
        # Pre-split name/path words per block (avoid re-splitting on every query)
        self._name_words: list[list[str]] = []
        self._path_words: list[list[str]] = []
        self._build()

    def _build(self) -> None:
        for i, block in enumerate(self._snippets):
            nw = _split_name(block.name)
            self._name_words.append(nw)
            # Also index the full lowercased symbol name as one token so
            # `qw == "focus_window"` queries hit immediately via the
            # candidate-selection union (line ~517) without needing fuzzy.
            self._name_index.setdefault(block.name.lower(), set()).add(i)
            for w in nw:
                self._name_index.setdefault(w, set()).add(i)
                # Also index stems and prefixes for fuzzy
                self._name_index.setdefault(_stem(w), set()).add(i)
                if len(w) >= 3:
                    self._name_index.setdefault(w[:3], set()).add(i)

            pw = [w for w in re.split(r"[_/\\\.\s]+", block.file_path.lower()) if w]
            self._path_words.append(pw)
            for w in pw:
                self._path_index.setdefault(w, set()).add(i)

            doc = (block.docstring or "").lower()
            for w in set(re.split(r"\W+", doc)):
                if len(w) > 2:
                    self._doc_index.setdefault(w, set()).add(i)

            self._kind_index.setdefault(block.kind.lower(), set()).add(i)

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

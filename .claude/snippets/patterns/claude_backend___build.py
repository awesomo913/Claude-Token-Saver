# From: claude_backend/search.py:514

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

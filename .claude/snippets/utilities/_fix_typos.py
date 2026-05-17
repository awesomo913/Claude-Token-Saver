# From: claude_backend/search.py:160
# Fix common typos using the dictionary, plus SequenceMatcher for unknown ones.

def _fix_typos(words: list[str]) -> list[str]:
    """Fix common typos using the dictionary, plus SequenceMatcher for unknown ones."""
    fixed = []
    # Build a vocabulary from concepts + domain names for fuzzy correction
    vocab = set()
    for concept_words in CONCEPTS.values():
        vocab.update(concept_words)
    vocab.update(CONCEPTS.keys())
    vocab.update(FILE_DOMAINS.values())

    for w in words:
        # Direct dictionary hit
        if w in _TYPO_FIXES:
            fixed.append(_TYPO_FIXES[w])
            continue

        # If the word is already in vocabulary, keep it
        if w in vocab:
            fixed.append(w)
            continue

        # Try fuzzy match against vocabulary for unknown typos
        best_word = w
        best_score = 0.0
        for v in vocab:
            if abs(len(v) - len(w)) > 2:
                continue  # skip words too different in length
            ratio = SequenceMatcher(None, w, v).ratio()
            if ratio > best_score and ratio > 0.75:
                best_score = ratio
                best_word = v

        fixed.append(best_word)
    return fixed

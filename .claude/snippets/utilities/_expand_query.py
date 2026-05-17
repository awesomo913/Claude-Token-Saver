# From: claude_backend/search.py:322
# Turn a sloppy English query into expanded search terms.

def _expand_query(raw_query: str) -> list[str]:
    """Turn a sloppy English query into expanded search terms.

    - Splits into words (caps at 20 most distinctive words)
    - Adds synonym expansions
    - Adds stems
    """
    # Clean and split
    raw = raw_query.lower().strip()
    raw = re.sub(r"[^a-z0-9_ ]", " ", raw)
    all_words = [w for w in raw.split() if len(w) > 2]

    # Only strip TRUE filler — keep words that carry intent (build, make, show, find, etc.)
    _FILLER = {"the", "and", "for", "that", "with", "this", "from", "will", "have",
               "been", "they", "which", "their", "into", "also", "than", "them",
               "each", "all", "one", "not", "but", "are", "was", "were", "has",
               "had", "its", "our", "who", "very", "just", "really", "actually",
               "basically", "should", "could", "would", "about", "being", "whole",
               "thing", "some", "other", "every", "still", "already", "right"}
    words = [w for w in all_words if w not in _FILLER][:20]
    if not words:
        words = all_words[:10]  # fallback: use everything rather than return nothing

    # Fix typos BEFORE expansion so corrected words hit concepts properly
    words = _fix_typos(words)

    expanded: set[str] = set(words)

    for word in words:
        # Add stem
        expanded.add(_stem(word))

        # Add concept synonyms
        # Direct concept match
        if word in CONCEPTS:
            expanded.update(CONCEPTS[word])
        # Reverse: word is a synonym of a concept
        if word in _WORD_TO_CONCEPTS:
            for concept in _WORD_TO_CONCEPTS[word]:
                expanded.update(CONCEPTS[concept])

        # Also try stem against concepts
        stemmed = _stem(word)
        if stemmed in CONCEPTS:
            expanded.update(CONCEPTS[stemmed])
        if stemmed in _WORD_TO_CONCEPTS:
            for concept in _WORD_TO_CONCEPTS[stemmed]:
                expanded.update(CONCEPTS[concept])

    return list(expanded)

# From: claude_backend/search.py:610
# Search snippets with fuzzy matching, synonyms, and intent detection.

def smart_search(
    snippets: list[CodeBlock],
    query: str,
    max_results: int = 15,
    min_score: float = 3.0,
) -> list[tuple[float, CodeBlock]]:
    """Search snippets with fuzzy matching, synonyms, and intent detection.

    Automatically builds and caches an inverted index for performance.
    On a 10K-block project, first query builds the index (~200ms),
    subsequent queries use it (~5ms each).
    """
    global _cached_index, _cached_snippets_id, _cached_snippets_len

    if not query.strip() or not snippets:
        return []

    # Rebuild index if list identity OR length changed (catches mutations)
    snippets_id = id(snippets)
    snippets_len = len(snippets)
    if (_cached_index is None
            or _cached_snippets_id != snippets_id
            or _cached_snippets_len != snippets_len):
        _cached_index = SearchIndex(snippets)
        _cached_snippets_id = snippets_id
        _cached_snippets_len = snippets_len

    # Scale min_score by query length — short queries need lower threshold
    raw = re.sub(r"[^a-z0-9_ ]", " ", query.lower().strip())
    raw_words = [w for w in raw.split() if len(w) > 2]
    effective_min = max(2.0, min_score * len(raw_words) / 4)

    return _cached_index.search(query, max_results, effective_min)

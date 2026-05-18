# From: claude_backend/search.py:405
# Score a code block against expanded query terms.

def score_block(block: CodeBlock, query_terms: list[str], raw_words: list[str]) -> float:
    """Score a code block against expanded query terms.

    Designed for NON-CODERS: matches vague descriptions, penalizes
    deep session artifacts, boosts well-documented code.

    Returns 0.0+ score. Higher = more relevant.
    """
    score = 0.0

    name_lower = block.name.lower()
    name_words = _split_name(block.name)

    # Strong boost when the query mentions the symbol verbatim
    # ("how does focus_window work"). Without this, raw_words=["focus_window"]
    # never matched name_words=["focus","window"] for the +10 per-word path.
    if name_lower in raw_words:
        score += 25.0

    doc_lower = (block.docstring or "").lower()
    doc_words = set(re.split(r"\W+", doc_lower)) if doc_lower else set()
    path_lower = block.file_path.lower()
    path_words = re.split(r"[_/\\\.\s]+", path_lower)

    kind_lower = block.kind.lower()

    # ── Score against raw user words (highest priority) ──
    for qw in raw_words:
        # Exact name word match
        if qw in name_words:
            score += 10.0
        else:
            best = max((_fuzzy_match(qw, nw) for nw in name_words), default=0.0)
            if best > 0.5:
                score += best * 8.0

        # Docstring: check both substring AND word-level match
        if qw in doc_lower:
            score += 4.0
        elif _stem(qw) in doc_words:
            score += 3.0
        elif any(_fuzzy_match(qw, dw) > 0.7 for dw in doc_words):
            score += 2.0  # fuzzy docstring match for typos

        # Path
        if qw in path_words:
            score += 3.0
        else:
            best_p = max((_fuzzy_match(qw, pw) for pw in path_words), default=0.0)
            if best_p > 0.6:
                score += best_p * 2.5

    # ── Score against expanded synonym terms (lower weight) ──
    expanded_only = [t for t in query_terms if t not in raw_words]
    content_matches = 0
    for term in expanded_only:
        if term in name_words:
            score += 3.0
        if term in doc_words:
            score += 1.5
        if term in path_words:
            score += 1.0
        if term in kind_lower:
            score += 2.0
        if content_matches < 5 and term in block.source.lower()[:500]:
            score += 0.5
            content_matches += 1

    # ── BONUSES for non-coder friendliness ──

    # Documented code is more useful to beginners
    if block.docstring and len(block.docstring) > 20:
        score *= 1.3  # 30% boost for well-documented blocks

    # ── PENALTIES ──

    # Deep paths = session artifacts, old generated code — less relevant
    depth = path_lower.count("/")
    if depth > 3:
        score *= 0.5  # halve score for deeply nested files
    elif depth > 2:
        score *= 0.75

    # Penalize code from sessions/ClaudeProjects (old generated artifacts)
    if "sessions/" in path_lower or "claudeprojects" in path_lower:
        score *= 0.3  # heavy penalty — these are old copies, not the real code

    return score

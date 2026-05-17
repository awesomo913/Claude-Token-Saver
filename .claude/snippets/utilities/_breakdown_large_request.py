# From: claude_backend/gui.py:1212
# Break a large request into sub-tasks, search each, deduplicate.

    def _breakdown_large_request(
        self, text: str, snippets: list
    ) -> list[tuple[float, CodeBlock]]:
        """Break a large request into sub-tasks, search each, deduplicate.

        For a 300-word request, this:
        1. Splits into sentences / clauses
        2. Searches each chunk separately (focused matches)
        3. Deduplicates and ranks by total relevance
        4. Returns top results
        """
        import re as _re

        # Split on sentence boundaries and conjunctions
        chunks = _re.split(r'[.!?\n]+|(?:,\s*(?:and|also|plus|then|while)\s)', text)
        chunks = [c.strip() for c in chunks if len(c.strip()) > 10]

        # Also try splitting on "and" / "also" for run-on sentences
        if len(chunks) <= 2 and len(text) > 200:
            chunks = _re.split(r'\band\b|\balso\b|\bplus\b|\bthen\b', text)
            chunks = [c.strip() for c in chunks if len(c.strip()) > 10]

        # Cap at 8 sub-searches
        chunks = chunks[:8]

        # Search each chunk, accumulate scores per block
        block_scores: dict[str, tuple[float, CodeBlock]] = {}
        for chunk in chunks:
            results = smart_search(snippets, chunk, max_results=4, min_score=3.0)
            for score, block in results:
                key = f"{block.name}:{block.file_path}"
                if key in block_scores:
                    old_score = block_scores[key][0]
                    block_scores[key] = (old_score + score, block)
                else:
                    block_scores[key] = (score, block)

        # Sort by accumulated score, return top results
        ranked = sorted(block_scores.values(), key=lambda x: -x[0])
        return ranked[:10]

# From: classifier/splitter.py:80
# Split on sentence boundaries, preserving code blocks as single units.

    @staticmethod
    def _split_sentences(prompt: str) -> list[str]:
        """Split on sentence boundaries, preserving code blocks as single units."""
        # Extract code blocks first
        code_blocks: list[str] = []
        def _replace_code(m: re.Match) -> str:
            code_blocks.append(m.group(0))
            return f"__CODE_BLOCK_{len(code_blocks) - 1}__"

        text = re.sub(r"```[\s\S]*?```", _replace_code, prompt)

        # Split on sentence endings
        raw = re.split(r"(?<=[.!?])\s+", text.strip())
        # Also split on newlines that look like list items or new thoughts
        expanded: list[str] = []
        for chunk in raw:
            parts = re.split(r"\n(?=[-*\d]\.?\s|\n)", chunk)
            expanded.extend(p.strip() for p in parts if p.strip())

        # Restore code blocks
        result: list[str] = []
        for s in expanded:
            for i, block in enumerate(code_blocks):
                s = s.replace(f"__CODE_BLOCK_{i}__", block)
            result.append(s)

        return result

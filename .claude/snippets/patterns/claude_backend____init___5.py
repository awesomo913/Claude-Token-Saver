# From: claude_backend/search.py:502

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

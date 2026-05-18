# From: classifier/classifier.py:25

    def __init__(self, keywords_path: Path | None = None) -> None:
        path = keywords_path or _DEFAULT_KEYWORDS
        self._keywords = self._load_keywords(path)

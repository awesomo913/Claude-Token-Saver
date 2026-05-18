# From: smart_router.py:33

    def __init__(self) -> None:
        if not SMART_ROUTER_AVAILABLE:
            raise RuntimeError(f"classifier not importable: {_import_error}")
        self._classifier = PromptClassifier()
        self._splitter = TaskSplitter(self._classifier)

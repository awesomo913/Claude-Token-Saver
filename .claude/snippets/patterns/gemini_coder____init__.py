# From: gemini_coder/config.py:29

    def __init__(self) -> None:
        self._path = get_config_dir() / "config.json"
        self.config = self._load()

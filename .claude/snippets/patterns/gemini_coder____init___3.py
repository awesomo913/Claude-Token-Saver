# From: gemini_coder/gemini_client.py:12

    def __init__(self, model: str = "gemini-2.0-flash", temperature: float = 0.9):
        self.model = model
        self.temperature = temperature
        self.history: List[dict] = []

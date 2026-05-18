# From: gemini_coder/gemini_client.py:33

    def __init__(self, api_key: str = "", model: str = "gemini-2.0-flash", 
                 temperature: float = 0.9):
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.conversation = Conversation(model, temperature)

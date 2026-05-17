# From: broadcast.py:39
# Check if response contains code markers. Returns False when the AI

def _looks_like_code(text: str) -> bool:
    """Check if response contains code markers. Returns False when the AI
    has lost context and is producing random chat instead of code."""
    if not text or len(text.strip()) < 50:
        return False
    # Look for common code indicators
    markers = ["def ", "class ", "import ", "function ", "const ", "var ", "let ",
               "```", "return ", "if __name__", "#!/", "async ", "struct ", "#include",
               "from ", "self.", "console.", "print(", "for ", "while "]
    text_lower = text.lower()
    hits = sum(1 for m in markers if m.lower() in text_lower)
    return hits >= 2  # at least 2 code markers

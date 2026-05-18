# From: gemini_coder/safe_exec.py:35
# Extract code blocks from markdown text.

def extract_code_blocks(text: str) -> list[str]:
    """Extract code blocks from markdown text."""
    import re
    pattern = r'```(?:\w+)?\n(.*?)```'
    matches = re.findall(pattern, text, re.DOTALL)
    return [block.strip() for block in matches if block.strip()]

# From: gemini_coder/safe_exec.py:43
# Clean extracted code by removing common AI artifacts.

def clean_code(code: str) -> str:
    """Clean extracted code by removing common AI artifacts."""
    code = code.strip()
    
    if code.startswith("```"):
        lines = code.split('\n')
        code = '\n'.join(lines[1:] if lines[0].startswith("```") else lines)
    
    if code.endswith("```"):
        code = code[:-3].strip()
    
    return code

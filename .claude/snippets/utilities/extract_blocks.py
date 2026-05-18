# From: claude_backend/analyzers/code_extractor.py:214
# Extract code blocks based on file extension.

def extract_blocks(source: str, ext: str, file_path: str = "") -> list[CodeBlock]:
    """Extract code blocks based on file extension."""
    if ext == ".py":
        return extract_python_blocks(source, file_path)
    elif ext in (".js", ".ts", ".jsx", ".tsx"):
        return extract_js_blocks(source, file_path)
    return []

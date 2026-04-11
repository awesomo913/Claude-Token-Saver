# From: claude_backend/types.py:29

@dataclass
class CodeBlock:
    """An extracted code block (function, class, etc.)."""
    name: str
    kind: str              # "function", "async_function", "class", "method", "js_function"
    source: str            # Extracted source text
    start_line: int
    end_line: int
    docstring: Optional[str] = None
    decorators: list[str] = field(default_factory=list)
    file_path: str = ""

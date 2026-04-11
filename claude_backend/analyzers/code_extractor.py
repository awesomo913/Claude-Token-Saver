"""Code block extraction using AST for Python and state-machine for JS/TS."""

from __future__ import annotations

import ast
import logging
import re
from typing import Optional

from ..types import CodeBlock

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Python extraction via AST
# ---------------------------------------------------------------------------

def extract_python_blocks(source: str, file_path: str = "") -> list[CodeBlock]:
    """Extract functions and classes from Python source using AST.

    Falls back to returning the entire file as one block on parse failure.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        logger.debug("AST parse failed for %s: %s — skipping", file_path, e)
        return []  # Skip unparseable files — better than giant useless blocks

    lines = source.splitlines(keepends=True)
    blocks: list[CodeBlock] = []

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if not hasattr(node, "end_lineno") or node.end_lineno is None:
            continue

        start = node.lineno
        end = node.end_lineno

        # Include decorators
        if node.decorator_list:
            first_dec = node.decorator_list[0]
            start = min(start, first_dec.lineno)

        block_source = "".join(lines[start - 1 : end])

        kind = "class"
        if isinstance(node, ast.FunctionDef):
            kind = "function"
        elif isinstance(node, ast.AsyncFunctionDef):
            kind = "async_function"

        # Check if it's a method (parent is a ClassDef)
        for parent in ast.walk(tree):
            if isinstance(parent, ast.ClassDef):
                for child in ast.iter_child_nodes(parent):
                    if child is node:
                        kind = "method"
                        break

        docstring = ast.get_docstring(node)
        decorators = []
        for dec in node.decorator_list:
            if isinstance(dec, ast.Name):
                decorators.append(dec.id)
            elif isinstance(dec, ast.Attribute):
                decorators.append(ast.dump(dec))
            elif isinstance(dec, ast.Call):
                if isinstance(dec.func, ast.Name):
                    decorators.append(dec.func.id)

        blocks.append(CodeBlock(
            name=node.name,
            kind=kind,
            source=block_source,
            start_line=start,
            end_line=end,
            docstring=docstring,
            decorators=decorators,
            file_path=file_path,
        ))

    return blocks


# ---------------------------------------------------------------------------
# JS/TS extraction via state-machine brace matching
# ---------------------------------------------------------------------------

# Pattern to find function/class/const declarations
_JS_DECL_RE = re.compile(
    r"(?:^|\n)\s*(?:export\s+)?(?:default\s+)?"
    r"(?:(?:async\s+)?function\s+\w+|class\s+\w+|"
    r"(?:const|let|var)\s+\w+\s*=\s*(?:(?:async\s+)?\(|(?:async\s+)?function))"
)


def extract_js_blocks(source: str, file_path: str = "") -> list[CodeBlock]:
    """Extract function and class blocks from JS/TS source.

    Uses a string-literal-aware brace matcher to avoid being tricked
    by braces inside strings or comments.
    """
    blocks: list[CodeBlock] = []

    for match in _JS_DECL_RE.finditer(source):
        # Find the opening brace after the declaration
        pos = match.end()
        brace_pos = source.find("{", pos)
        if brace_pos == -1:
            continue

        end_pos = _find_matching_brace(source, brace_pos)
        if end_pos == -1:
            continue

        block_text = source[match.start():end_pos + 1].strip()
        start_line = source[:match.start()].count("\n") + 1
        end_line = source[:end_pos + 1].count("\n") + 1

        # Extract name from the declaration
        name = _extract_js_name(block_text)

        blocks.append(CodeBlock(
            name=name,
            kind="js_function",
            source=block_text,
            start_line=start_line,
            end_line=end_line,
            file_path=file_path,
        ))

    return blocks


def _find_matching_brace(source: str, open_pos: int) -> int:
    """Find the closing brace matching the one at open_pos.

    Tracks state to skip braces inside strings, template literals, and comments.
    """
    state = "normal"
    depth = 1
    i = open_pos + 1
    length = len(source)

    while i < length and depth > 0:
        ch = source[i]
        prev = source[i - 1] if i > 0 else ""

        if state == "normal":
            if ch == "/" and i + 1 < length:
                next_ch = source[i + 1]
                if next_ch == "/":
                    state = "line_comment"
                    i += 2
                    continue
                elif next_ch == "*":
                    state = "block_comment"
                    i += 2
                    continue
            if ch == '"':
                state = "double_quote"
            elif ch == "'":
                state = "single_quote"
            elif ch == "`":
                state = "template_literal"
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return i

        elif state == "double_quote":
            if ch == '"' and prev != "\\":
                state = "normal"

        elif state == "single_quote":
            if ch == "'" and prev != "\\":
                state = "normal"

        elif state == "template_literal":
            if ch == "`" and prev != "\\":
                state = "normal"

        elif state == "line_comment":
            if ch == "\n":
                state = "normal"

        elif state == "block_comment":
            if ch == "/" and prev == "*":
                state = "normal"

        i += 1

    return -1


_JS_NAME_RE = re.compile(r"(?:function|class|const|let|var)\s+(\w+)")


def _extract_js_name(block: str) -> str:
    """Extract the name from a JS declaration."""
    m = _JS_NAME_RE.search(block[:200])
    return m.group(1) if m else "anonymous"


# ---------------------------------------------------------------------------
# Unified extraction interface
# ---------------------------------------------------------------------------

def extract_blocks(source: str, ext: str, file_path: str = "") -> list[CodeBlock]:
    """Extract code blocks based on file extension."""
    if ext == ".py":
        return extract_python_blocks(source, file_path)
    elif ext in (".js", ".ts", ".jsx", ".tsx"):
        return extract_js_blocks(source, file_path)
    return []

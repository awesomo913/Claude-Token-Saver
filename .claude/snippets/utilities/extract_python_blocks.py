# From: claude_backend/analyzers/code_extractor.py:19
# Extract functions and classes from Python source using AST.

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

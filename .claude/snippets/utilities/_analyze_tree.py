# From: claude_backend/analyzers/pattern_detector.py:59
# Walk an AST and tally convention indicators.

def _analyze_tree(tree: ast.AST, source: str, counts: dict) -> None:
    """Walk an AST and tally convention indicators."""
    for node in ast.walk(tree):
        # Imports
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "pathlib" or alias.name.startswith("pathlib."):
                    counts["pathlib"] += 1
                if alias.name == "os.path" or alias.name == "os":
                    counts["os_path"] += 1
                if alias.name == "logging":
                    counts["logging_module"] += 1

        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module == "pathlib" or module.startswith("pathlib."):
                counts["pathlib"] += 1
            if module in ("os", "os.path"):
                counts["os_path"] += 1
            if module == "logging":
                counts["logging_module"] += 1
            if node.level and node.level > 0:
                counts["relative_import"] += 1
            else:
                counts["absolute_import"] += 1

        # Type hints on functions
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            has_hints = node.returns is not None or any(
                a.annotation is not None for a in node.args.args
            )
            if has_hints:
                counts["type_hints"] += 1
            else:
                counts["no_type_hints"] += 1

        # Exception handling
        elif isinstance(node, ast.ExceptHandler):
            if node.type is None:
                counts["bare_except"] += 1
            elif isinstance(node.type, ast.Name) and node.type.id == "Exception":
                counts["broad_except"] += 1
            else:
                counts["specific_except"] += 1

        # Print calls
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == "print":
                counts["print_calls"] += 1

    # F-strings (check source text since AST doesn't distinguish)
    if "f'" in source or 'f"' in source:
        counts["f_string"] += 1
    if ".format(" in source:
        counts["format_method"] += 1
    if "% " in source or "%s" in source or "%d" in source:
        counts["percent_format"] += 1

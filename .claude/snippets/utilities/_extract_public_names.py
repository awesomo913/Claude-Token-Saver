# From: claude_backend/analyzers/structure_mapper.py:50
# Extract non-private top-level names (functions, classes, assignments).

def _extract_public_names(tree: ast.Module) -> list[str]:
    """Extract non-private top-level names (functions, classes, assignments)."""
    names: list[str] = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if not node.name.startswith("_"):
                names.append(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and not target.id.startswith("_"):
                    names.append(target.id)
    return names

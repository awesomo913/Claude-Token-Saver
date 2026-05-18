# From: claude_backend/analyzers/structure_mapper.py:64
# Extract imports that reference project-internal modules.

def _extract_internal_imports(tree: ast.Module, project_name: str) -> list[str]:
    """Extract imports that reference project-internal modules."""
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.level and node.level > 0:
                # Relative import
                module = node.module or ""
                imports.append(f".{'.' * (node.level - 1)}{module}")
            elif node.module and project_name and node.module.startswith(project_name):
                imports.append(node.module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if project_name and alias.name.startswith(project_name):
                    imports.append(alias.name)
    return imports

# From: claude_backend/analyzers/structure_mapper.py:89
# Build a dict mapping module path -> list of internal imports.

def build_import_graph(modules: list[ModuleInfo]) -> dict[str, list[str]]:
    """Build a dict mapping module path -> list of internal imports."""
    return {m.path: m.imports for m in modules if m.imports}

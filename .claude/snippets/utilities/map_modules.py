# From: claude_backend/analyzers/structure_mapper.py:13
# Analyze Python files to extract module-level information.

def map_modules(entries: list[FileEntry], project_name: str = "") -> list[ModuleInfo]:
    """Analyze Python files to extract module-level information."""
    modules: list[ModuleInfo] = []

    py_files = [e for e in entries if e.ext == ".py"]

    for entry in py_files:
        # Skip test files and __pycache__
        if "test" in entry.path.split("/")[0:1]:
            continue

        try:
            tree = ast.parse(entry.content)
        except SyntaxError:
            modules.append(ModuleInfo(
                path=entry.path,
                line_count=entry.line_count,
            ))
            continue

        docstring = ast.get_docstring(tree)
        public_names = _extract_public_names(tree)
        imports = _extract_internal_imports(tree, project_name)
        is_entry = _is_entry_point(entry.content)

        modules.append(ModuleInfo(
            path=entry.path,
            docstring=docstring,
            public_names=public_names,
            imports=imports,
            entry_point=is_entry,
            line_count=entry.line_count,
        ))

    return modules

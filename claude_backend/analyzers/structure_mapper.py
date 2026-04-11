"""Map project structure: modules, imports, public API, entry points."""

from __future__ import annotations

import ast
import logging

from ..types import FileEntry, ModuleInfo

logger = logging.getLogger(__name__)


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


def _is_entry_point(source: str) -> bool:
    """Check if source contains common entry point patterns."""
    markers = ['if __name__ == "__main__"', "if __name__ == '__main__'",
               "def main(", "app.mainloop(", "app.run("]
    return any(m in source for m in markers)


def build_import_graph(modules: list[ModuleInfo]) -> dict[str, list[str]]:
    """Build a dict mapping module path -> list of internal imports."""
    return {m.path: m.imports for m in modules if m.imports}

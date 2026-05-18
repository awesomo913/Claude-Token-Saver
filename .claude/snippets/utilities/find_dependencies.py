# From: claude_backend/scanners/project.py:234
# Extract dependency names from requirements.txt or pyproject.toml.

def find_dependencies(root: Path) -> list[str]:
    """Extract dependency names from requirements.txt or pyproject.toml."""
    deps: list[str] = []

    req = root / "requirements.txt"
    if req.is_file():
        try:
            for line in req.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and not line.startswith("-"):
                    name = line.split(">=")[0].split("==")[0].split("<")[0].split("[")[0].strip()
                    if name:
                        deps.append(name)
        except OSError:
            pass

    pyproject = root / "pyproject.toml"
    if pyproject.is_file():
        try:
            text = pyproject.read_text(encoding="utf-8")
            in_deps = False
            for line in text.splitlines():
                stripped = line.strip()
                if stripped.startswith("dependencies"):
                    in_deps = True
                    continue
                if in_deps:
                    if stripped.startswith("]"):
                        in_deps = False
                        continue
                    if stripped.startswith('"') or stripped.startswith("'"):
                        name = stripped.strip("\"', ")
                        name = name.split(">=")[0].split("==")[0].split("<")[0].split("[")[0].strip()
                        if name:
                            deps.append(name)
        except OSError:
            pass

    return deps

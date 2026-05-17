# From: claude_backend/config.py:43
# Load config with layered defaults.

def load_config(
    config_path: Optional[Path] = None,
    project_path: Optional[Path] = None,
) -> ScanConfig:
    """Load config with layered defaults.

    Priority: built-in defaults < global < project < explicit path.
    """
    merged: dict = {}

    # Layer 1: global config
    global_cfg = Path.home() / ".claude" / "backend_config.json"
    if global_cfg.is_file():
        merged.update(_load_json(global_cfg))

    # Layer 2: project config
    if project_path:
        project_cfg = project_path / ".claude" / "backend_config.json"
        if project_cfg.is_file():
            merged.update(_load_json(project_cfg))

    # Layer 3: explicit config file
    if config_path and config_path.is_file():
        merged.update(_load_json(config_path))

    return _dict_to_config(merged)

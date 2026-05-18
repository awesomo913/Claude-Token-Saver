# From: claude_backend/generators/claude_md.py:118
# Generate a 2-level directory tree.

def _structure_section(analysis: ProjectAnalysis) -> str:
    """Generate a 2-level directory tree."""
    lines = ["## Structure\n", "```"]

    # Build tree from file paths
    dirs: dict[str, dict[str, int]] = {}
    for f in analysis.files:
        parts = f.path.split("/")
        if len(parts) >= 2:
            top = parts[0]
            if top not in dirs:
                dirs[top] = {}
            if len(parts) >= 3:
                sub = parts[1]
                dirs[top][sub] = dirs[top].get(sub, 0) + 1
            else:
                dirs[top]["(files)"] = dirs[top].get("(files)", 0) + 1
        else:
            dirs.setdefault("(root)", {})
            dirs["(root)"]["(files)"] = dirs["(root)"].get("(files)", 0) + 1

    for top_dir in sorted(dirs.keys()):
        if top_dir == "(root)":
            continue
        sub_count = sum(dirs[top_dir].values())
        lines.append(f"{top_dir}/  ({sub_count} files)")
        subs = dirs[top_dir]
        for sub_name in sorted(subs.keys())[:8]:
            if sub_name == "(files)":
                continue
            lines.append(f"  {sub_name}/  ({subs[sub_name]} files)")

    lines.extend(["```", ""])
    return "\n".join(lines)

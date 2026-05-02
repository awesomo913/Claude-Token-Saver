# From: patch_upstream.py:131

def patch_build_script() -> bool:
    f = ROOT / "build_exe.py"
    if not f.exists():
        return False
    src = _read(f)
    changed = False

    # Fix 1: use launcher instead of gui.py
    if '"claude_backend/gui.py",' in src:
        src = src.replace(
            '"claude_backend/gui.py",',
            '"launch_token_saver.py",',
        )
        changed = True

    # Fix 2: add missing hidden imports (tokenizer, search)
    if '"--hidden-import", "claude_backend.tokenizer"' not in src:
        src = src.replace(
            '"--hidden-import", "claude_backend.generators.snippet_library",',
            '"--hidden-import", "claude_backend.generators.snippet_library",\n'
            '    "--hidden-import", "claude_backend.tokenizer",\n'
            '    "--hidden-import", "claude_backend.search",',
            1,
        )
        changed = True

    if changed:
        _write(f, src)
        print("  [ok]   build-script patched")
        return True
    print("  [skip] build-script already patched")
    return False

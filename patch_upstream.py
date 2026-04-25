"""Auto-patcher: applies known fixes to upstream code before building.

Run this after pulling updates from the repo. Idempotent — safe to run repeatedly.
Each patch checks for the bug signature first; only applies if the bug is present.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _write(p: Path, s: str) -> None:
    p.write_text(s, encoding="utf-8")


# ─────────────────────────────────────────────────────────────────────
# PATCH 1: Copy button off-screen (tkinter pack order bug in gui.py)
# ─────────────────────────────────────────────────────────────────────
#   SYMPTOM: The "Copy Complete Prompt to Clipboard" button doesn't show on
#            maximized windows. `bar` is packed AFTER `split` which has
#            expand=True — split claims all leftover space, pushing bar off.
#   FIX:     Move bar creation/pack BEFORE split, use side="bottom".
# ─────────────────────────────────────────────────────────────────────
def patch_copy_button_layout() -> bool:
    f = ROOT / "claude_backend" / "gui.py"
    if not f.exists():
        return False
    src = _read(f)

    # Already patched? Look for the marker comment.
    if "pack FIRST with side=bottom" in src:
        print("  [skip] copy-button-layout already patched")
        return False

    # Detect buggy pattern
    bad_split = (
        '        # ═══ MAIN SPLIT: queue | preview ═══\n'
        '        split = ctk.CTkFrame(fr, fg_color="transparent")\n'
        '        split.pack(fill="both", expand=True, padx=20, pady=(0, 6))'
    )
    bad_bar = (
        '        # ═══ BOTTOM: Big copy button ═══\n'
        '        bar = ctk.CTkFrame(fr, fg_color=C["card"], corner_radius=8, border_width=2, border_color=C["accent"])\n'
        '        bar.pack(fill="x", padx=20, pady=(0, 12))\n'
        '        bi = ctk.CTkFrame(bar, fg_color="transparent"); bi.pack(fill="x", padx=12, pady=10)\n'
        '        ctk.CTkButton(bi, text="Copy Complete Prompt to Clipboard",\n'
        '                      font=(F, 15, "bold"), fg_color=C["accent"],\n'
        '                      hover_color=C["accent2"], height=48, width=360,\n'
        '                      command=self._copy_context).pack(side="left", padx=(0, 12))\n'
        '        ctk.CTkButton(bi, text="Snippets Only", font=(F, 11), fg_color=C["bg2"],\n'
        '                      height=34, width=120, command=self._copy_raw).pack(side="left")'
    )

    if bad_split not in src or bad_bar not in src:
        print("  [warn] copy-button-layout: pattern not found (upstream may have changed)")
        return False

    # Move bar block to BEFORE split, change to side="bottom"
    fixed_split = (
        '        # ═══ BOTTOM: Big copy button (pack FIRST with side=bottom so it always shows) ═══\n'
        '        bar = ctk.CTkFrame(fr, fg_color=C["card"], corner_radius=8, border_width=2, border_color=C["accent"])\n'
        '        bar.pack(side="bottom", fill="x", padx=20, pady=(0, 12))\n'
        '        bi = ctk.CTkFrame(bar, fg_color="transparent"); bi.pack(fill="x", padx=12, pady=10)\n'
        '        ctk.CTkButton(bi, text="Copy Complete Prompt to Clipboard",\n'
        '                      font=(F, 15, "bold"), fg_color=C["accent"],\n'
        '                      hover_color=C["accent2"], height=48, width=360,\n'
        '                      command=self._copy_context).pack(side="left", padx=(0, 12))\n'
        '        ctk.CTkButton(bi, text="Snippets Only", font=(F, 11), fg_color=C["bg2"],\n'
        '                      height=34, width=120, command=self._copy_raw).pack(side="left")\n'
        '\n'
        '        # ═══ MAIN SPLIT: queue | preview ═══\n'
        '        split = ctk.CTkFrame(fr, fg_color="transparent")\n'
        '        split.pack(fill="both", expand=True, padx=20, pady=(0, 6))'
    )

    src = src.replace(bad_split, fixed_split, 1)
    src = src.replace("\n" + bad_bar, "", 1)
    _write(f, src)
    print("  [ok]   copy-button-layout patched")
    return True


# ─────────────────────────────────────────────────────────────────────
# PATCH 2: PyInstaller launcher (relative import bug)
# ─────────────────────────────────────────────────────────────────────
#   SYMPTOM: "ImportError: attempted relative import with no known parent
#            package" when running the exe. PyInstaller runs gui.py as a
#            script, so `from .backend import ...` fails.
#   FIX:     Create launch_token_saver.py wrapper that adds sys.path first.
# ─────────────────────────────────────────────────────────────────────
def patch_launcher_wrapper() -> bool:
    f = ROOT / "launch_token_saver.py"
    if f.exists():
        return False
    _write(f, '''"""Entry point for PyInstaller — bootstraps claude_backend as a package."""

import sys
from pathlib import Path

# When frozen by PyInstaller, _MEIPASS points to the temp extraction dir.
# claude_backend is bundled as data there, so add it to sys.path.
if getattr(sys, 'frozen', False):
    base = Path(sys._MEIPASS)
    sys.path.insert(0, str(base))
else:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from claude_backend.gui import main

if __name__ == "__main__":
    main()
''')
    print("  [ok]   launcher-wrapper created")
    return True


# ─────────────────────────────────────────────────────────────────────
# PATCH 3: build_exe.py uses launcher + includes all hidden imports
# ─────────────────────────────────────────────────────────────────────
#   SYMPTOM: Build succeeds but exe fails with ImportError for tokenizer,
#            search, or other submodules; or gui.py as entry point breaks
#            relative imports.
#   FIX:     Use launch_token_saver.py as entry, add missing hidden imports.
# ─────────────────────────────────────────────────────────────────────
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
            '"launch_token_saver.py",'
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


# ─────────────────────────────────────────────────────────────────────
def main() -> int:
    print("Applying upstream patches...")
    patch_launcher_wrapper()
    patch_build_script()
    patch_copy_button_layout()
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

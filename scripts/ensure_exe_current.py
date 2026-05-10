"""Rebuild ClaudeTokenSaver.exe if any source file is newer than the
shipped exe.

Run after every git commit / pull / local edit to keep
~/Desktop/ClaudeTokenSaver/ClaudeTokenSaver.exe in sync with the source
tree without remembering to invoke `python build_exe.py` by hand.

Behaviour:
  - Walk every relevant source path (claude_backend/, ai/, classifier/,
    extension_native_bridge/, extensions/, ui/, scripts/build_exe.py,
    requirements.txt, the spec file, top-level launchers).
  - Compare the newest mtime against the shipped exe's mtime.
  - If src is newer, kill any running ClaudeTokenSaver.exe (so
    PyInstaller can overwrite the file), invoke build_exe.py, then
    optionally relaunch.
  - If the shipped exe is missing, always build.
  - If everything is up-to-date, exit 0 silently.

Flags:
  --no-relaunch     don't restart ClaudeTokenSaver.exe after a rebuild.
  --no-kill         skip the pre-build kill step.
  --quiet           suppress "up-to-date" message.
  --force           rebuild even if up-to-date.

Designed to be called from a git post-commit / post-merge hook AND
from the user's shortcut wrapper. Never raises — exits 0 on success,
non-zero only on PyInstaller failure.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DESKTOP = Path.home() / "Desktop"
DEPLOY_DIR = DESKTOP / "ClaudeTokenSaver"   # matches build_exe.py DEPLOY_TARGETS
SHIPPED = DEPLOY_DIR / "ClaudeTokenSaver.exe"

# Source paths whose mtime drives rebuild decisions. Keep narrow — adding
# tests/ or docs/ here would force a rebuild after every test-only or
# docs-only change. `scripts/ensure_exe_current.py` is intentionally
# excluded so editing the hook itself doesn't trigger a rebuild loop.
SRC_GLOBS: tuple[str, ...] = (
    "claude_backend/**/*.py",
    "ai/**/*.py",
    "classifier/**/*.py",
    "extension_native_bridge/**/*.py",
    "extensions/**/*.py",
    "gemini_coder/**/*.py",
    "gemini_coder_web/**/*.py",
    "ui/**/*.py",
    "launch_token_saver.py",
    "launch_tray.py",
    "broadcast.py",
    "patch_upstream.py",
    "build_exe.py",
    "requirements.txt",
    "pyproject.toml",
)


def _newest_src_mtime() -> float:
    newest = 0.0
    for pattern in SRC_GLOBS:
        for p in ROOT.glob(pattern):
            try:
                m = p.stat().st_mtime
            except OSError:
                continue
            if m > newest:
                newest = m
    return newest


def _exe_mtime() -> float:
    if not SHIPPED.is_file():
        return 0.0
    try:
        return SHIPPED.stat().st_mtime
    except OSError:
        return 0.0


def _kill_running() -> int:
    """Stop every ClaudeTokenSaver.exe instance so PyInstaller can
    overwrite the shipped binary. Returns the count killed."""
    count = 0
    if not sys.platform.startswith("win"):
        return count
    try:
        proc = subprocess.run(
            ["taskkill", "/F", "/IM", "ClaudeTokenSaver.exe"],
            capture_output=True, text=True, timeout=10,
        )
        if proc.returncode == 0 and "SUCCESS" in proc.stdout.upper():
            for line in proc.stdout.splitlines():
                if "SUCCESS" in line.upper():
                    count += 1
    except Exception:  # noqa: BLE001
        pass
    return count


def _build() -> int:
    """Invoke build_exe.py at repo root. Returns its exit code."""
    cmd = [sys.executable, str(ROOT / "build_exe.py")]
    proc = subprocess.run(cmd, cwd=str(ROOT))
    return int(proc.returncode)


def _relaunch() -> None:
    if not SHIPPED.is_file():
        return
    if not sys.platform.startswith("win"):
        return
    try:
        subprocess.Popen(
            ["cmd", "/c", "start", "", str(SHIPPED)],
            cwd=str(DEPLOY_DIR),
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except Exception:  # noqa: BLE001
        pass


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-relaunch", action="store_true")
    parser.add_argument("--no-kill", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    src_mtime = _newest_src_mtime()
    exe_mtime = _exe_mtime()
    if not args.force and exe_mtime and src_mtime <= exe_mtime:
        if not args.quiet:
            age = int(exe_mtime - src_mtime)
            print(
                f"[ensure_exe_current] up-to-date "
                f"(exe is {age}s newer than newest src)"
            )
        return 0

    reason = "missing" if not exe_mtime else f"src newer by {int(src_mtime - exe_mtime)}s"
    if args.force:
        reason = "forced"
    print(f"[ensure_exe_current] rebuilding ClaudeTokenSaver.exe ({reason})")

    if not args.no_kill:
        n = _kill_running()
        if n:
            print(
                f"[ensure_exe_current] killed {n} running "
                f"ClaudeTokenSaver.exe instance(s)"
            )
            time.sleep(1)  # let Windows release the file lock

    rc = _build()
    if rc != 0:
        print(
            f"[ensure_exe_current] build_exe.py exited {rc}",
            file=sys.stderr,
        )
        return rc

    if not args.no_relaunch:
        _relaunch()
        print("[ensure_exe_current] relaunched ClaudeTokenSaver.exe")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

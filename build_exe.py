"""Build script for Claude Token Saver standalone exe."""
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

# Optional: after build, copy dist/ClaudeTokenSaver into each folder (replaces existing).
# Leave empty for CI / clones; add local Path(...) entries on your machine only.
DEPLOY_TARGETS: list[Path] = []

# Auto-apply upstream patches before building (idempotent)
_patcher = HERE / "patch_upstream.py"
if _patcher.exists():
    subprocess.run([sys.executable, str(_patcher)], check=True)

cmd = [
    sys.executable, "-m", "PyInstaller",
    "--noconfirm",
    "--onedir",
    "--windowed",
    "--name", "ClaudeTokenSaver",
    "--add-data", "claude_backend;claude_backend",
    "--hidden-import", "claude_backend",
    "--hidden-import", "claude_backend.gui",
    "--hidden-import", "claude_backend.backend",
    "--hidden-import", "claude_backend.config",
    "--hidden-import", "claude_backend.types",
    "--hidden-import", "claude_backend.storage",
    "--hidden-import", "claude_backend.manifest",
    "--hidden-import", "claude_backend.search",
    "--hidden-import", "claude_backend.prompt_builder",
    "--hidden-import", "claude_backend.tracker",
    "--hidden-import", "claude_backend.ollama_manager",
    "--hidden-import", "claude_backend.scanners",
    "--hidden-import", "claude_backend.scanners.project",
    "--hidden-import", "claude_backend.scanners.local",
    "--hidden-import", "claude_backend.scanners.github",
    "--hidden-import", "claude_backend.analyzers",
    "--hidden-import", "claude_backend.analyzers.code_extractor",
    "--hidden-import", "claude_backend.analyzers.pattern_detector",
    "--hidden-import", "claude_backend.analyzers.structure_mapper",
    "--hidden-import", "claude_backend.generators",
    "--hidden-import", "claude_backend.generators.claude_md",
    "--hidden-import", "claude_backend.generators.memory_files",
    "--hidden-import", "claude_backend.generators.snippet_library",
    "--hidden-import", "claude_backend.tokenizer",
    "--hidden-import", "claude_backend.search",
    "--collect-submodules", "customtkinter",
    "launch_token_saver.py",
]

print("Building ClaudeTokenSaver.exe ...")
print(" ".join(cmd[:6]) + " ...")
subprocess.run(cmd, check=True)

# Deploy the fresh build to every target folder (replacing any existing copy)
_dist = HERE / "dist" / "ClaudeTokenSaver"
if _dist.exists():
    print("\nDeploying to target folders:")
    for target in DEPLOY_TARGETS:
        try:
            if target.exists():
                shutil.rmtree(target)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(_dist, target)
            print(f"  [ok] {target}")
        except Exception as e:
            print(f"  [fail] {target}  ({e})")

print("\nDone! Output in dist/ClaudeTokenSaver/")

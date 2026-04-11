"""Build script for Claude Token Saver standalone exe."""
import subprocess
import sys

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
    "--collect-submodules", "customtkinter",
    "claude_backend/gui.py",
]

print("Building ClaudeTokenSaver.exe ...")
print(" ".join(cmd[:6]) + " ...")
subprocess.run(cmd, check=True)
print("Done! Output in dist/ClaudeTokenSaver/")

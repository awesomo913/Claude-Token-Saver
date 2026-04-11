#!/usr/bin/env python3
"""Smoke test for Literag integration and end-to-end flow.

Creates a temporary configuration that points to the local literag sample,
runs the Claude backend CLI once, then runs it again to validate delta behavior.
Prints a short summary of results.
"""
import json
import os
import sys
import shutil
import tempfile
import subprocess
from pathlib import Path


def run_cli(config_path: str, project_name: str) -> dict:
    # Run as a module to support relative imports inside claude_backend
    cmd = [sys.executable, "-m", "claude_backend.cli", config_path, project_name]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, check=False, timeout=300)
    out = res.stdout
    try:
        data = json.loads(out)
    except Exception:
        data = {"raw_output": out}
    return data


def main():
    literag_dir = Path("tests/literag_sample").resolve()
    if not literag_dir.exists():
        print("Cannot find tests/literag_sample; ensure repo layout matches and run from repo root.")
        sys.exit(2)

    tmp_session = tempfile.mkdtemp(prefix="claude_smoke_")
    try:
        config_content = f"""
session_root: '{tmp_session}'
claude_projects_dir: ClaudeProjects
github_token: ""
local_sources:
  - paths:
      - '{str(literag_dir)}'
        extensions: [".py", ".js", ".md", ".json", ".txt"]
ai_root: "C:/Users/default.LAPTOP-S2O9G7EP/Desktop/AI"
ai_extensions:
  - .py
  - .js
  - .md
  - .json
  - .txt
"""
        config_path = os.path.join(tmp_session, "config.yaml")
        # Debug: print the config content to verify YAML correctness
        print("[SMOKE TEST] Generated config content:\n" + config_content)
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(config_content)

        project_name = "smoke_literag"
        print(f"Running first pass with config: {config_path}, project: {project_name}")
        first = run_cli(config_path, project_name)
        print("First run result:")
        print(json.dumps(first, indent=2))

        print("Running second pass to test delta behavior...")
        second = run_cli(config_path, project_name)
        print("Second run result:")
        print(json.dumps(second, indent=2))
        print("Smoke test complete.")
    finally:
        shutil.rmtree(tmp_session, ignore_errors=True)


if __name__ == "__main__":
    main()

"""
Writes the Native Messaging host manifest and registry key for Google Chrome (current user).

Usage:
  py -3 install_host_windows.py <chrome_extension_id> [<path_to_host.json_output>]

The extension ID is the 32-char ID from chrome://extensions (Developer mode) for
the unpacked "Claude Bridge" extension.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HOST_NAME = "com.claudetools.bridge"


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: install_host_windows.py <extension_id> [output_json_path]", file=sys.stderr)
        return 1

    ext_id = sys.argv[1].strip()
    if not ext_id or len(ext_id) < 20:
        print("Error: extension id looks invalid", file=sys.stderr)
        return 1

    script_dir = Path(__file__).resolve().parent
    host_dir = script_dir.parent / "host"
    run_cmd = (host_dir / "run_host.cmd").resolve()
    if not run_cmd.is_file():
        print(f"Error: missing {run_cmd}", file=sys.stderr)
        return 1

    win_path = str(run_cmd).replace("/", "\\")
    out_json = (
        Path(sys.argv[2]).resolve()
        if len(sys.argv) > 2
        else (host_dir / f"{HOST_NAME}.json")
    )

    body = {
        "name": HOST_NAME,
        "path": win_path,
        "type": "stdio",
        "allowed_origins": [f"chrome-extension://{ext_id}/"],
    }
    out_json.write_text(json.dumps(body, indent=2), encoding="utf-8")
    print(f"Wrote: {out_json}")

    if sys.platform != "win32":
        print("Not on Windows — registry not updated. On Linux/macOS use manifest path docs for Chrome.")
        return 0

    reg_path = r"HKCU\Software\Google\Chrome\NativeMessagingHosts\{}".format(HOST_NAME)
    val = str(out_json)
    cmd = ["reg", "add", reg_path, "/ve", "/d", val, "/f"]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"Registry: {reg_path} -> {val}")
    except subprocess.CalledProcessError as e:
        print(f"reg add failed: {e.stderr or e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

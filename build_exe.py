"""Build script for Claude Token Saver (standalone Windows exe)."""
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
APP_NAME = "ClaudeTokenSaver"
ICON = HERE / "assets" / "claudetokensaver.ico"
ICON_SOURCE = Path(r"C:\Users\computer\Desktop\AI\cursor_token_saver\assets\claudetokensaver.ico")
DESKTOP_LNK = Path.home() / "Desktop" / f"{APP_NAME}.lnk"


def _default_deploy_targets() -> list[Path]:
    """Deploy the --onedir build into the workspace-standard My Apps folder."""
    return [Path.home() / "Desktop" / "My Apps" / APP_NAME]


DEPLOY_TARGETS: list[Path] = _default_deploy_targets()


def _ensure_icon() -> Path | None:
    ICON.parent.mkdir(parents=True, exist_ok=True)
    if ICON_SOURCE.exists():
        shutil.copy2(ICON_SOURCE, ICON)
    return ICON if ICON.exists() else None


def _create_shortcut(exe_path: Path) -> None:
    icon_loc = ICON if ICON.exists() else exe_path
    ps = (
        "$ws = New-Object -ComObject WScript.Shell; "
        f"$lnk = $ws.CreateShortcut('{DESKTOP_LNK}'); "
        f"$lnk.TargetPath = '{exe_path}'; "
        f"$lnk.WorkingDirectory = '{exe_path.parent}'; "
        f"$lnk.IconLocation = '{icon_loc},0'; "
        "$lnk.Description = 'Claude Token Saver'; "
        "$lnk.Save();"
    )
    subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
        check=True,
    )
    print(f"  [ok] shortcut -> {DESKTOP_LNK}")


def _deploy(dist_dir: Path) -> None:
    print("\nDeploying to target folders:")
    for target in DEPLOY_TARGETS:
        try:
            if target.exists():
                shutil.rmtree(target)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(dist_dir, target)
            print(f"  [ok] {target}")
        except PermissionError:
            subprocess.run(
                ["taskkill", "/F", "/IM", f"{APP_NAME}.exe"],
                capture_output=True,
                text=True,
            )
            time.sleep(2)
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(dist_dir, target)
            print(f"  [ok] {target} (after kill)")
        except Exception as e:
            print(f"  [fail] {target}  ({e})")
            raise

    deployed_exe = DEPLOY_TARGETS[0] / f"{APP_NAME}.exe"
    if deployed_exe.exists():
        _create_shortcut(deployed_exe)


def main() -> None:
    patcher = HERE / "patch_upstream.py"
    if patcher.exists():
        subprocess.run([sys.executable, str(patcher)], check=True)

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name", APP_NAME,
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
        "--hidden-import", "claude_backend.tray",
        "--hidden-import", "claude_backend.welcome",
        "--hidden-import", "claude_backend.prefs",
        "--hidden-import", "claude_backend.single_instance",
        "--hidden-import", "claude_backend.session_launcher",
        "--hidden-import", "claude_backend.http_server",
        "--hidden-import", "claude_backend.overlay",
        "--hidden-import", "claude_backend.session_detector",
        "--hidden-import", "claude_backend.hotkey",
        "--hidden-import", "keyboard",
        "--hidden-import", "pyautogui",
        "--hidden-import", "pyperclip",
        "--hidden-import", "pystray",
        "--hidden-import", "pystray._win32",
        "--collect-submodules", "customtkinter",
        "--collect-submodules", "pystray",
        "--collect-submodules", "keyboard",
        "launch_token_saver.py",
    ]
    icon = _ensure_icon()
    if icon:
        cmd[8:8] = ["--icon", str(icon)]

    print(f"Building {APP_NAME}.exe ...")
    print(" ".join(cmd[:8]) + " ...")
    subprocess.run(cmd, check=True, cwd=str(HERE))

    dist_dir = HERE / "dist" / APP_NAME
    if dist_dir.exists():
        _deploy(dist_dir)

    print(f"\nDone! Output in dist/{APP_NAME}/")


if __name__ == "__main__":
    main()

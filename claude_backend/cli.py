"""CLI interface for Claude token saver."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from .backend import ClaudeContextManager
from .config import ScanConfig, load_config


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="claude-backend",
        description="Claude Code context generator -- save tokens by pre-staging project context.",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Debug logging")
    parser.add_argument("--config", type=Path, help="Path to JSON config file")

    sub = parser.add_subparsers(dest="command", required=True)

    # bootstrap
    p_boot = sub.add_parser("bootstrap", help="Full scan + generate all context files")
    p_boot.add_argument("project_path", type=Path, help="Path to target project")
    p_boot.add_argument("--no-claude-md", action="store_true")
    p_boot.add_argument("--no-memory", action="store_true")
    p_boot.add_argument("--no-snippets", action="store_true")
    p_boot.add_argument("--dry-run", action="store_true", help="Analyze only, don't write")

    # prep
    p_prep = sub.add_parser("prep", help="Delta update -- regenerate only stale files")
    p_prep.add_argument("project_path", type=Path, help="Path to target project")
    p_prep.add_argument("--force", action="store_true", help="Regenerate all")
    p_prep.add_argument("--quiet", action="store_true", help="Suppress output (for hook use)")

    # scan
    p_scan = sub.add_parser("scan", help="Analyze project and print report")
    p_scan.add_argument("project_path", type=Path, help="Path to target project")

    # status
    p_stat = sub.add_parser("status", help="Show generated file state")
    p_stat.add_argument("project_path", type=Path, help="Path to target project")

    # clean
    p_clean = sub.add_parser("clean", help="Remove generated artifacts")
    p_clean.add_argument("project_path", type=Path, help="Path to target project")
    p_clean.add_argument("--yes", action="store_true", help="Skip confirmation")

    # tray — system tray icon (passive reminder + quick actions)
    sub.add_parser("tray", help="Run system tray icon")

    # doctor — audits installation health (settings.json, prefs, exe, hooks, shortcut)
    sub.add_parser("doctor", help="Audit Token Saver installation health")

    args = parser.parse_args(argv)

    # Configure logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(levelname)s: %(message)s",
        stream=sys.stderr,
    )

    # tray has no project_path / no config — handle before loading config
    if args.command == "tray":
        from .tray import run as _tray_run
        return _tray_run()

    # doctor: same — no project, no config needed
    if args.command == "doctor":
        return _run_doctor()

    # Load config
    config = load_config(
        config_path=args.config,
        project_path=getattr(args, "project_path", None),
    )

    # Apply CLI overrides
    if hasattr(args, "no_claude_md") and args.no_claude_md:
        config.generate_claude_md = False
    if hasattr(args, "no_memory") and args.no_memory:
        config.generate_memory = False
    if hasattr(args, "no_snippets") and args.no_snippets:
        config.generate_snippets = False

    mgr = ClaudeContextManager(config)

    if args.command == "bootstrap":
        if args.dry_run:
            analysis = mgr.analyze(args.project_path)
            _print_analysis(analysis)
            return 0
        result = mgr.bootstrap(args.project_path)
        print(json.dumps({
            "command": "bootstrap",
            "written": len(result.files_written),
            "skipped": len(result.files_skipped),
            "errors": result.errors,
            "summary": result.summary,
        }, indent=2))

    elif args.command == "prep":
        result = mgr.prep(args.project_path, force=getattr(args, "force", False))
        if not getattr(args, "quiet", False):
            print(json.dumps({
                "command": "prep",
                "updated": len(result.files_updated),
                "skipped": len(result.files_skipped),
                "errors": result.errors,
                "summary": result.summary,
            }, indent=2))

    elif args.command == "scan":
        analysis = mgr.analyze(args.project_path)
        _print_analysis(analysis)

    elif args.command == "status":
        info = mgr.status(args.project_path)
        print(json.dumps(info, indent=2))

    elif args.command == "clean":
        if not args.yes:
            print("This will remove generated CLAUDE.md sections, memory files, and snippets.")
            try:
                answer = input("Continue? [y/N] ").strip().lower()
                if answer != "y":
                    print("Aborted.")
                    return 1
            except (EOFError, KeyboardInterrupt):
                print("\nAborted.")
                return 1

        removed = mgr.clean(args.project_path)
        print(f"Removed {len(removed)} items:")
        for r in removed:
            print(f"  - {r}")

    return 0


def _run_doctor() -> int:
    """Audit Token Saver installation health.

    Returns 0 if all CRITICAL checks pass, 1 otherwise. Informational
    items (e.g. tray running, opt-in launcher hook) never trigger
    failure exit code. Output is ASCII-safe (Windows cp1252 console).
    """
    from . import auto_inject
    from .prefs import PREFS_PATH, Prefs
    from .single_instance import is_locked

    # Each check: (label, ok, note, critical)
    checks: list[tuple[str, bool, str, bool]] = []

    # 1. settings.json (critical)
    prep = auto_inject.check_status()
    if not prep["settings_exists"]:
        checks.append(("settings.json exists", False,
                       str(auto_inject.SETTINGS_PATH), True))
    elif not prep["settings_valid"]:
        checks.append(("settings.json valid JSON", False,
                       prep["error"], True))
    else:
        checks.append(("settings.json exists + valid", True, "", True))

    # 2. Prep hook (critical if user has it)
    if prep["settings_valid"]:
        checks.append((
            "Auto-Inject prep hook installed",
            prep["installed"],
            "" if prep["installed"] else "(run 'install' from GUI to enable)",
            True,
        ))

    # 3. Prefs file (critical)
    if PREFS_PATH.is_file():
        try:
            p = Prefs.load()
            checks.append((
                "Prefs file readable",
                True,
                f"auto_launch={p.auto_launch_gui_on_session} minimized={p.auto_launch_minimized}",
                True,
            ))
        except Exception as e:
            checks.append(("Prefs file readable", False, str(e), True))
            p = Prefs()  # for subsequent checks
    else:
        checks.append((
            "Prefs file exists",
            True,  # not a fail; will be created on first save
            f"(absent; will create on first save)",
            False,
        ))
        p = Prefs()

    # 4. Launcher hooks — both SessionStart and UserPromptSubmit. Compare
    #    against toggle state (critical if mismatched).
    launch = auto_inject.check_launcher_status()
    prompt = auto_inject.check_prompt_status()
    expected = p.auto_launch_gui_on_session
    if expected:
        checks.append((
            "SessionStart launcher hook (toggle ON)",
            launch["installed"],
            "" if launch["installed"] else "(missing -- click Install in Settings)",
            True,
        ))
        checks.append((
            "UserPromptSubmit launcher hook (toggle ON)",
            prompt["installed"],
            "" if prompt["installed"] else "(missing -- existing sessions won't auto-launch)",
            True,
        ))
    else:
        checks.append((
            "SessionStart launcher hook (toggle OFF)",
            not launch["installed"],
            "(installed but toggle is OFF)" if launch["installed"] else "",
            True,
        ))
        checks.append((
            "UserPromptSubmit launcher hook (toggle OFF)",
            not prompt["installed"],
            "(installed but toggle is OFF)" if prompt["installed"] else "",
            True,
        ))

    # 5. Exe path (informational unless user expects it)
    desktop_exe = Path.home() / "Desktop" / "ClaudeTokenSaver" / "ClaudeTokenSaver.exe"
    checks.append((
        "Desktop exe present",
        desktop_exe.is_file(),
        str(desktop_exe) if desktop_exe.is_file() else f"missing: {desktop_exe}",
        False,  # informational -- user might run from source
    ))

    # 6. Autostart shortcut (informational)
    if sys.platform == "win32":
        import os
        appdata = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
        lnk = (Path(appdata) / "Microsoft" / "Windows" / "Start Menu"
               / "Programs" / "Startup" / "ClaudeTokenSaverTray.lnk")
        checks.append((
            "Autostart shortcut",
            lnk.is_file(),
            str(lnk) if lnk.is_file() else f"missing: {lnk}",
            False,
        ))

    # 7. Tray running (informational only)
    tray_running = is_locked("ClaudeTokenSaverTray")
    checks.append((
        "Tray currently running",
        tray_running,
        "" if tray_running else "(start via tray icon shortcut or 'python -m claude_backend tray')",
        False,
    ))

    # 8. Backup count (informational)
    try:
        backups = list(auto_inject.SETTINGS_PATH.parent.glob("settings.json.backup-*"))
        checks.append((
            "settings.json backups (max 3 expected)",
            len(backups) <= 3,
            f"{len(backups)} backup(s)",
            False,
        ))
    except OSError:
        pass

    # Print report (ASCII only -- avoids cp1252 console encoding errors)
    print("\n=== Token Saver doctor ===\n")
    critical_fails = 0
    info_fails = 0
    for label, ok, note, critical in checks:
        if ok:
            mark = "[OK]   "
        elif critical:
            mark = "[FAIL] "
            critical_fails += 1
        else:
            mark = "[INFO] "
            info_fails += 1
        sep = " -- " if note else ""
        print(f"  {mark}{label}{sep}{note}")

    print()
    if critical_fails == 0:
        if info_fails:
            print(f"All critical checks passed. ({info_fails} informational notice(s) above.)")
        else:
            print("All checks passed.")
        return 0
    print(f"{critical_fails} critical check(s) failed. See [FAIL] entries above.")
    return 1


def _print_analysis(analysis) -> None:
    """Print a human-readable analysis report."""
    print(f"\n=== Project: {analysis.name} ===")
    print(f"Path: {analysis.root}")
    print(f"Files: {len(analysis.files)}")

    if analysis.language_stats:
        print("\nLanguages:")
        for ext, count in list(analysis.language_stats.items())[:10]:
            print(f"  {ext}: {count}")

    if analysis.entry_points:
        print(f"\nEntry points: {', '.join(analysis.entry_points[:5])}")

    if analysis.dependencies:
        print(f"Dependencies: {', '.join(analysis.dependencies[:10])}")

    if analysis.key_files:
        print(f"Key files: {', '.join(analysis.key_files)}")

    print(f"\nModules: {len(analysis.modules)}")
    print(f"Code blocks: {len(analysis.blocks)}")

    conv = analysis.conventions
    if conv.samples_analyzed > 0:
        print(f"\nConventions ({conv.samples_analyzed} files sampled):")
        print(f"  Path handling: {conv.path_style}")
        print(f"  Type hints: {conv.type_hints}")
        print(f"  Formatting: {conv.string_format}")
        print(f"  Error handling: {conv.error_handling}")
        print(f"  Logging: {conv.logging_style}")
        print(f"  Imports: {conv.import_style}")


if __name__ == "__main__":
    sys.exit(main())

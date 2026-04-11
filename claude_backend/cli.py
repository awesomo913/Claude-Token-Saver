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

    args = parser.parse_args(argv)

    # Configure logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(levelname)s: %(message)s",
        stream=sys.stderr,
    )

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
        result = mgr.prep(args.project_path)
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

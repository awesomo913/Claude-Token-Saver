"""Grade /improve token-saving + retrieval quality.

For each test prompt:
  1. Call _gather_snippet_context() — measure tokens injected.
  2. Compare to baseline: total tokens of the source file containing
     the ground-truth symbol the user would otherwise need to paste.
  3. Record hit = did the expected symbol appear in injected snippets.

Aggregate: mean savings, hit rate, per-prompt breakdown.

Run:
    python scripts/grade_savings.py
    python scripts/grade_savings.py --project "C:/path/to/other/project"
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from claude_backend.http_server import _gather_snippet_context  # noqa: E402
from claude_backend.tokenizer import count_tokens                # noqa: E402


# Test set targets THIS project's own symbols. Each entry:
#   prompt           — realistic user query
#   expected_symbol  — substring we want to see in injected snippet names
#   ground_truth_rel — repo-relative path Claude would otherwise need
TESTS: list[dict] = [
    {
        "prompt": "how does smart_search rank code snippets",
        "expected_symbol": "smart_search",
        "ground_truth_rel": "claude_backend/search.py",
    },
    {
        "prompt": "where does the token tracker write savings to disk",
        "expected_symbol": "TokenTracker",
        "ground_truth_rel": "claude_backend/tracker.py",
    },
    {
        "prompt": "how do I detect which ai site a url belongs to",
        "expected_symbol": "detect_ai_site",
        "ground_truth_rel": "cdp_test.py",
    },
    {
        "prompt": "how does the http server handle improve requests",
        "expected_symbol": "run_improve_pipeline",
        "ground_truth_rel": "claude_backend/http_server.py",
    },
    {
        "prompt": "how is the project picker rendered in the overlay",
        "expected_symbol": "_show_picker",
        "ground_truth_rel": "claude_backend/overlay.py",
    },
    {
        "prompt": "how does memory file generation work",
        "expected_symbol": "generate_memory_files",
        "ground_truth_rel": "claude_backend/generators/memory_files.py",
    },
    {
        "prompt": "how does the gui pick up improve pending file from disk",
        "expected_symbol": "_handle_pending",
        "ground_truth_rel": "claude_backend/gui.py",
    },
    {
        "prompt": "how does the focus_window helper bring a window forward",
        "expected_symbol": "focus_window",
        "ground_truth_rel": "browser_actions.py",
    },
    {
        "prompt": "how do I send a prompt to an ai chat tab",
        "expected_symbol": "send_message",
        "ground_truth_rel": "browser_actions.py",
    },
    {
        "prompt": "how does the tray menu build its right click items",
        "expected_symbol": "build_menu",
        "ground_truth_rel": "claude_backend/tray.py",
    },
]


def _safe_count(path: Path) -> int:
    try:
        return count_tokens(path.read_text(encoding="utf-8", errors="replace"))
    except OSError:
        return 0


def grade(project_path: Path) -> dict:
    results: list[dict] = []
    for t in TESTS:
        prompt = t["prompt"]
        expected = t["expected_symbol"]
        gt_rel = t["ground_truth_rel"]
        gt_file = project_path / gt_rel

        code_context, n_blocks, n_tokens = _gather_snippet_context(
            str(project_path), prompt,
        )
        baseline = _safe_count(gt_file)

        ctx_l = code_context.lower() if code_context else ""
        # Two hit semantics:
        #   strict: exact expected symbol name shows up in injected code
        #   area:   any snippet came from the ground-truth file path
        # area-OK matters because retrieval often returns "right area,
        # adjacent symbol" which is still useful for Claude.
        hit_strict = expected.lower() in ctx_l
        hit_area = gt_rel.lower().replace("\\", "/") in ctx_l.replace("\\", "/")
        hit = hit_strict or hit_area
        savings_pct = (
            round(100.0 * (1.0 - (n_tokens / baseline)), 1)
            if baseline > 0 else 0.0
        )

        results.append({
            "prompt": prompt,
            "expected": expected,
            "hit": hit,
            "hit_strict": hit_strict,
            "hit_area": hit_area,
            "snippets": n_blocks,
            "injected_tokens": n_tokens,
            "baseline_tokens": baseline,
            "savings_pct": savings_pct,
        })

    hits = sum(1 for r in results if r["hit"])
    hits_strict = sum(1 for r in results if r["hit_strict"])
    hits_area = sum(1 for r in results if r["hit_area"])
    served = sum(1 for r in results if r["snippets"] > 0)
    avg_savings = (
        round(sum(r["savings_pct"] for r in results if r["baseline_tokens"] > 0)
              / max(1, sum(1 for r in results if r["baseline_tokens"] > 0)), 1)
    )
    total_injected = sum(r["injected_tokens"] for r in results)
    total_baseline = sum(r["baseline_tokens"] for r in results)
    overall_savings_pct = (
        round(100.0 * (1.0 - (total_injected / total_baseline)), 1)
        if total_baseline > 0 else 0.0
    )

    return {
        "project": str(project_path),
        "test_count": len(TESTS),
        "hits": hits,
        "hits_strict": hits_strict,
        "hits_area": hits_area,
        "served": served,
        "hit_rate_pct": round(100.0 * hits / len(TESTS), 1),
        "hit_strict_pct": round(100.0 * hits_strict / len(TESTS), 1),
        "hit_area_pct": round(100.0 * hits_area / len(TESTS), 1),
        "served_rate_pct": round(100.0 * served / len(TESTS), 1),
        "mean_per_prompt_savings_pct": avg_savings,
        "weighted_overall_savings_pct": overall_savings_pct,
        "total_injected_tokens": total_injected,
        "total_baseline_tokens": total_baseline,
        "results": results,
    }


def _print_report(report: dict) -> None:
    print("\n=== /improve grader ===\n")
    print(f"Project: {report['project']}")
    print(f"Tests: {report['test_count']}")
    print(f"Served (any snippet injected): "
          f"{report['served']}/{report['test_count']} "
          f"({report['served_rate_pct']}%)")
    print(f"Hits (strict OR area): "
          f"{report['hits']}/{report['test_count']} "
          f"({report['hit_rate_pct']}%)")
    print(f"  - strict (exact symbol in snippet):  "
          f"{report['hits_strict']}/{report['test_count']} "
          f"({report['hit_strict_pct']}%)")
    print(f"  - area (any snippet from target file): "
          f"{report['hits_area']}/{report['test_count']} "
          f"({report['hit_area_pct']}%)")
    print(f"Mean per-prompt savings: {report['mean_per_prompt_savings_pct']}%")
    print(f"Weighted overall savings: {report['weighted_overall_savings_pct']}%")
    print(f"Total injected tokens:  {report['total_injected_tokens']:,}")
    print(f"Total baseline tokens:  {report['total_baseline_tokens']:,}\n")
    print(f"  {'STRICT':<6}  {'AREA':<4}  {'snips':>5}  {'inj':>6}  "
          f"{'base':>6}  {'save%':>6}  prompt")
    for r in report["results"]:
        s = "yes" if r["hit_strict"] else "no"
        a = "yes" if r["hit_area"] else "no"
        print(f"  {s:<6}  {a:<4}  {r['snippets']:>5}  "
              f"{r['injected_tokens']:>6}  "
              f"{r['baseline_tokens']:>6}  "
              f"{r['savings_pct']:>5}%  "
              f"{r['prompt'][:60]}")
    print()


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--project",
        type=Path,
        default=REPO_ROOT,
        help="Project root (default: this repo)",
    )
    p.add_argument(
        "--json", action="store_true", help="Emit JSON instead of table",
    )
    args = p.parse_args()
    report = grade(args.project.resolve())
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        _print_report(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Review all sessions, calculate real savings, find improvements."""
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

tracker_path = Path.home() / ".claude" / "token_savings.jsonl"
events = []
for line in tracker_path.read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if line:
        events.append(json.loads(line))

# ── Session timeline ──
print("SESSION REVIEW")
print("=" * 65)
print(f"Total events: {len(events)}")

by_day = defaultdict(list)
for e in events:
    day = e.get("ts", "")[:10]
    by_day[day].append(e)

total_tok_sent = 0
total_items = 0
total_copies = 0

for day in sorted(by_day):
    evts = by_day[day]
    builds = [e for e in evts if e["op"] == "context_build"]
    tok = sum(e.get("tokens", 0) for e in builds)
    items = 0
    for e in builds:
        d = e.get("detail", "")
        if "items=" in d:
            try:
                items += int(d.split("items=")[1].split(",")[0].split(")")[0])
            except (ValueError, IndexError):
                pass
    total_tok_sent += tok
    total_items += items
    total_copies += len(builds)
    print(f"  {day}: {len(builds):>2} copies, {items:>4} snippets, {tok:>8,} tok sent")

print(f"\nTotals: {total_copies} copies, {total_items:,} snippets, {total_tok_sent:,} tok sent")

# ── What Claude would have read ──
print("\n\nTOKEN SAVINGS CALCULATION")
print("-" * 65)

# Conservative: each snippet came from a file, avg file = 3000 tokens
# 60% unique files (dedup for same-file snippets)
avg_file = 3000
unique_ratio = 0.6
would_read = int(total_items * unique_ratio * avg_file)
saved = max(0, would_read - total_tok_sent)

print(f"Snippets referenced:    {total_items:,}")
print(f"Unique files (est 60%): {int(total_items * unique_ratio):,}")
print(f"Avg file size:          {avg_file:,} tokens")
print(f"Claude would read:      {would_read:,} tokens")
print(f"You sent:               {total_tok_sent:,} tokens")
print(f"SAVED:                  {saved:,} tokens ({saved * 100 // max(would_read, 1)}%)")

# Session pre-load savings
# Each unique project-day session saves ~50K tokens (pre-loaded context vs scanning)
project_days = set()
for e in events:
    p = e.get("project", "")
    d = e.get("ts", "")[:10]
    if p:
        project_days.add((p, d))
session_savings = len(project_days) * 50_000
print(f"\nSession pre-load savings: {len(project_days)} sessions x ~50K = {session_savings:,} tokens")

grand = saved + session_savings
print(f"GRAND TOTAL SAVED:      {grand:,} tokens")
print(f"Opus value ($15/MTok):  ${grand * 15 / 1e6:.2f}")
print(f"Sonnet value ($3/MTok): ${grand * 3 / 1e6:.2f}")

# ── Per-project breakdown ──
print("\n\nPER-PROJECT BREAKDOWN")
print("-" * 65)
by_proj = defaultdict(lambda: {"copies": 0, "items": 0, "tok": 0})
for e in events:
    if e["op"] != "context_build":
        continue
    proj = e.get("project", "") or "(none)"
    by_proj[proj]["copies"] += 1
    by_proj[proj]["tok"] += e.get("tokens", 0)
    d = e.get("detail", "")
    if "items=" in d:
        try:
            by_proj[proj]["items"] += int(d.split("items=")[1].split(",")[0].split(")")[0])
        except (ValueError, IndexError):
            pass

for proj in sorted(by_proj, key=lambda p: -by_proj[p]["tok"]):
    d = by_proj[proj]
    w = int(d["items"] * unique_ratio * avg_file)
    s = max(0, w - d["tok"])
    print(f"  {proj:30s}: {d['copies']:>3} copies, {d['items']:>4} snippets, "
          f"sent {d['tok']:>8,}, saved {s:>9,} ({s * 100 // max(w, 1)}%)")

# ── Usage patterns ──
print("\n\nUSAGE PATTERNS & IMPROVEMENT OPPORTUNITIES")
print("-" * 65)

# Pattern 1: escalating item counts
large_copies = [e for e in events if e["op"] == "context_build"]
item_counts = []
for e in large_copies:
    d = e.get("detail", "")
    if "items=" in d:
        try:
            item_counts.append(int(d.split("items=")[1].split(",")[0].split(")")[0]))
        except (ValueError, IndexError):
            pass

if item_counts:
    avg_items = sum(item_counts) // len(item_counts)
    max_items = max(item_counts)
    over_20 = sum(1 for c in item_counts if c > 20)
    over_50 = sum(1 for c in item_counts if c > 50)
    print(f"  Avg snippets per copy:  {avg_items}")
    print(f"  Max snippets in one copy: {max_items}")
    print(f"  Copies with 20+ snippets: {over_20}/{len(item_counts)}")
    print(f"  Copies with 50+ snippets: {over_50}/{len(item_counts)}")
    if over_20 > len(item_counts) // 2:
        print("  ** ISSUE: Most copies have 20+ snippets = too much context")
        print("     The auto-find may be too aggressive. Consider:")
        print("     - Raising min_score threshold")
        print("     - Lowering max_results from 8 to 5")
        print("     - Making Quick Grab add 3 instead of 6 snippets")
    if over_50 > 3:
        print("  ** ISSUE: Multiple copies with 50+ snippets = massive prompts")
        print("     This wastes tokens. The compression should be more aggressive.")

# Pattern 2: empty copies
empty = sum(1 for c in item_counts if c == 0)
if empty:
    print(f"\n  Empty copies (0 snippets): {empty}")
    print("  These added prompt template overhead with no code context.")

# Pattern 3: duplicate consecutive copies
dupes = 0
for i in range(1, len(large_copies)):
    if (large_copies[i].get("tokens") == large_copies[i-1].get("tokens") and
            large_copies[i].get("project") == large_copies[i-1].get("project")):
        dupes += 1
if dupes:
    print(f"\n  Duplicate consecutive copies: {dupes}")
    print("  User clicked Copy multiple times on the same prompt.")

# Pattern 4: mode usage
modes = defaultdict(int)
for e in large_copies:
    d = e.get("detail", "")
    if "mode=" in d:
        mode = d.split("mode=")[1].split(",")[0]
        modes[mode] += 1
    elif "template=" in d:
        tmpl = d.split("template=")[1].split(",")[0]
        modes[tmpl] += 1

if modes:
    print(f"\n  Mode usage:")
    for mode, count in sorted(modes.items(), key=lambda x: -x[1]):
        print(f"    {mode}: {count} times")

# ── Improvement recommendations ──
print("\n\nRECOMMENDATIONS")
print("-" * 65)

recommendations = []
if avg_items > 15:
    recommendations.append(
        "REDUCE AUTO-FIND AGGRESSIVENESS: Avg {0} snippets/copy is too many. "
        "Lower max_results in auto-find from 8 to 5, raise min_score from 3.0 to 4.0.".format(avg_items))

if over_50 > 2:
    recommendations.append(
        "CAP QUEUE SIZE: {0} copies had 50+ snippets. Add a hard cap at 15 snippets "
        "in the queue, warn user when exceeded.".format(over_50))

if empty > 0:
    recommendations.append(
        "BLOCK EMPTY COPIES: {0} copies had 0 snippets. The Copy button should "
        "require at least 1 snippet or a request with text.".format(empty))

if dupes > 0:
    recommendations.append(
        "DEBOUNCE COPY BUTTON: {0} duplicate copies detected. Disable the button "
        "for 2 seconds after each click.".format(dupes))

if not recommendations:
    recommendations.append("No major issues detected. Usage patterns are healthy.")

for i, rec in enumerate(recommendations, 1):
    print(f"  {i}. {rec}")

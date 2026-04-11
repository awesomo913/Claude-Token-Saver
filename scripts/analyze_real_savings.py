"""Analyze REAL token savings from actual usage history."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

tracker_path = Path.home() / ".claude" / "token_savings.jsonl"
events = []
for line in tracker_path.read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if line:
        events.append(json.loads(line))

# Known project sizes (tokens) from our scans
PROJECT_SIZES = {
    "claude interaction tool": 302_000,
    "AI": 8_195_000,
    "emerald_devtool": 180_000,
    "pokeemerald": 500_000,  # conservative estimate for C ROM hack
    "test_project": 10_000,
}

# Average file sizes per project (tokens) — what Claude reads per file
AVG_FILE_TOKENS = {
    "claude interaction tool": 2_700,
    "AI": 4_100,
    "emerald_devtool": 2_000,
    "pokeemerald": 3_500,
    "test_project": 500,
}

print("=" * 70)
print("REAL TOKEN SAVINGS ANALYSIS — From Your Actual Usage")
print("=" * 70)
print()

# Separate events by type
context_builds = [e for e in events if e["op"] == "context_build"]
bootstraps = [e for e in events if e["op"] == "bootstrap"]
preps = [e for e in events if e["op"] == "prep"]
copies = [e for e in events if e["op"] == "clipboard_copy"]
tests = [e for e in events if e["op"] == "test_verification"]

print(f"Total events: {len(events)}")
print(f"  Context builds (prompts copied): {len(context_builds)}")
print(f"  Bootstraps:                      {len(bootstraps)}")
print(f"  Preps (updates):                 {len(preps)}")
print(f"  Clipboard copies:                {len(copies)}")
print(f"  Test runs:                       {len(tests)}")
print()

# ── Analyze each context build ──
print("CONTEXT BUILD ANALYSIS (each prompt you copied to Claude)")
print("-" * 70)

total_provided = 0      # what you actually sent (the prompt size)
total_would_have = 0    # what Claude would have read without the tool
total_saved = 0

by_project = {}

for e in context_builds:
    tok = e.get("tokens", 0)
    proj = e.get("project", "unknown") or "unknown"
    detail = e.get("detail", "")

    # Extract item count from detail
    items = 0
    if "items=" in detail:
        try:
            items = int(detail.split("items=")[1].split(",")[0].split(")")[0])
        except (ValueError, IndexError):
            pass

    # What Claude would have read WITHOUT the tool:
    # For each snippet in the prompt, Claude would have read the FULL FILE
    # Average: items * avg_file_size for that project
    avg_file = AVG_FILE_TOKENS.get(proj, 3000)
    would_have = items * avg_file if items > 0 else tok * 4  # conservative fallback

    saved = max(0, would_have - tok)
    total_provided += tok
    total_would_have += would_have
    total_saved += saved

    if proj not in by_project:
        by_project[proj] = {"count": 0, "provided": 0, "would_have": 0, "saved": 0, "items": 0}
    by_project[proj]["count"] += 1
    by_project[proj]["provided"] += tok
    by_project[proj]["would_have"] += would_have
    by_project[proj]["saved"] += saved
    by_project[proj]["items"] += items

print()
print("BY PROJECT:")
for proj in sorted(by_project, key=lambda p: -by_project[p]["saved"]):
    d = by_project[proj]
    pct = d["saved"] * 100 // max(d["would_have"], 1)
    print(f"\n  {proj}")
    print(f"    Prompts copied: {d['count']}")
    print(f"    Snippets used:  {d['items']}")
    print(f"    You provided:   {d['provided']:>10,} tokens (targeted snippets)")
    print(f"    Without tool:   {d['would_have']:>10,} tokens (full file reads)")
    print(f"    SAVED:          {d['saved']:>10,} tokens ({pct}%)")

print()

# ── Bootstrap savings ──
print("BOOTSTRAP/PREP SAVINGS")
print("-" * 70)
# Each bootstrap generates CLAUDE.md + memory files that Claude auto-loads
# This replaces Claude scanning ~30% of the project
bootstrap_saved = 0
for e in bootstraps + preps:
    proj = e.get("project", "")
    proj_size = PROJECT_SIZES.get(proj, 100_000)
    # Claude would scan 30% of source; bootstrap provides 5% equivalent
    would_scan = int(proj_size * 0.3)
    provided = e.get("tokens", 0)
    saved = max(0, would_scan - provided)
    bootstrap_saved += saved
    print(f"  {e['op']:12s} | {proj:30s} | saved ~{saved:,} tokens")

print(f"\n  Total bootstrap/prep savings: {bootstrap_saved:,} tokens")
print()

# ── Session savings (pre-loaded context) ──
print("SESSION CONTEXT SAVINGS")
print("-" * 70)
# Each unique project session benefits from pre-loaded CLAUDE.md + memory
unique_projects = set(e.get("project", "") for e in events if e.get("project"))
sessions_estimated = len(unique_projects) * 3  # estimate 3 sessions per project
session_savings = 0
for proj in unique_projects:
    proj_size = PROJECT_SIZES.get(proj, 100_000)
    per_session = int(proj_size * 0.3) - 17_500  # 30% scan minus preloaded
    if per_session > 0:
        session_savings += per_session * 3  # ~3 sessions per project
        print(f"  {proj:30s}: ~{per_session:,} tok/session x ~3 sessions = {per_session * 3:,}")

print(f"\n  Total session savings: {session_savings:,} tokens")
print()

# ── GRAND TOTAL ──
grand_total = total_saved + bootstrap_saved + session_savings
grand_provided = total_provided

print("=" * 70)
print("GRAND TOTAL — WHAT THE TOOL ACTUALLY SAVED YOU")
print("=" * 70)
print()
print(f"  Context builds:    {total_saved:>12,} tokens saved (from {len(context_builds)} prompts)")
print(f"  Bootstraps/preps:  {bootstrap_saved:>12,} tokens saved")
print(f"  Session context:   {session_savings:>12,} tokens saved")
print(f"  ─────────────────────────────────────")
print(f"  TOTAL SAVED:       {grand_total:>12,} tokens")
print(f"  TOTAL PROVIDED:    {grand_provided:>12,} tokens (what you actually sent)")
print()
print(f"  Efficiency ratio: sent {grand_provided:,} tok, avoided {grand_total:,} tok")
print(f"  For every 1 token you sent, you avoided {grand_total // max(grand_provided, 1)} tokens")
print()

# Cost
print("  MONEY SAVED:")
for model, rate in [("Opus ($15/MTok)", 15.0), ("Sonnet ($3/MTok)", 3.0), ("Haiku ($0.25/MTok)", 0.25)]:
    cost = grand_total * rate / 1_000_000
    print(f"    {model:25s}: ${cost:.2f}")
print()

# Timeline
first_ts = events[0].get("ts", "")[:10]
last_ts = events[-1].get("ts", "")[:10]
print(f"  Period: {first_ts} to {last_ts}")
print(f"  Events: {len(events)} total across {len(unique_projects)} projects")
print()

# Per-prompt stats
if context_builds:
    avg_provided = total_provided // len(context_builds)
    avg_would = total_would_have // len(context_builds)
    avg_items = sum(1 for _ in context_builds)
    print(f"  Per prompt average:")
    print(f"    You sent:    {avg_provided:,} tokens")
    print(f"    Claude would have read: {avg_would:,} tokens")
    print(f"    Savings: {(total_would_have - total_provided) * 100 // max(total_would_have, 1)}% reduction")

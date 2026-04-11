"""Project weekly/monthly savings from actual usage data."""
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

by_day = defaultdict(lambda: {"prompts": 0, "tokens_sent": 0, "items": 0})
for e in events:
    if e["op"] != "context_build":
        continue
    day = e.get("ts", "")[:10]
    by_day[day]["prompts"] += 1
    by_day[day]["tokens_sent"] += e.get("tokens", 0)
    detail = e.get("detail", "")
    if "items=" in detail:
        try:
            by_day[day]["items"] += int(detail.split("items=")[1].split(",")[0].split(")")[0])
        except (ValueError, IndexError):
            pass

AVG_FILE = 3200

print("WEEKLY & MONTHLY USAGE PROJECTION")
print("=" * 60)
first = sorted(by_day)[0] if by_day else "?"
last = sorted(by_day)[-1] if by_day else "?"
print(f"Usage period: {first} to {last}")
print()

print("DAILY BREAKDOWN:")
print("-" * 60)
total_prompts = 0
total_sent = 0
total_items = 0
for day in sorted(by_day):
    d = by_day[day]
    would_have = d["items"] * AVG_FILE
    saved = max(0, would_have - d["tokens_sent"])
    print(f"  {day}: {d['prompts']:>2} prompts, {d['items']:>3} snippets, "
          f"sent {d['tokens_sent']:>7,} tok, saved ~{saved:>9,} tok")
    total_prompts += d["prompts"]
    total_sent += d["tokens_sent"]
    total_items += d["items"]

active_days = len(by_day)
total_would = total_items * AVG_FILE
total_saved = max(0, total_would - total_sent)

print()
print(f"TOTALS ({active_days} active days):")
print(f"  Prompts:        {total_prompts}")
print(f"  Snippets used:  {total_items}")
print(f"  Tokens sent:    {total_sent:,}")
print(f"  Tokens avoided: {total_saved:,}")

ppd = total_prompts / max(active_days, 1)
spd = total_saved / max(active_days, 1)
ipd = total_items / max(active_days, 1)
tpd = total_sent / max(active_days, 1)

print()
print("YOUR ACTUAL DAILY RATE:")
print("-" * 60)
print(f"  {ppd:.0f} prompts/day")
print(f"  {ipd:.0f} snippets/day")
print(f"  {tpd:,.0f} tokens sent/day")
print(f"  {spd:,.0f} tokens saved/day")

# Weekly (5 work days)
ws = spd * 5
session_weekly = 75_000 * 5  # pre-loaded context savings
wt = ws + session_weekly

print()
print("WEEKLY PROJECTION (5 work days):")
print("-" * 60)
print(f"  From prompts:   {ws:>10,.0f} tokens saved")
print(f"  From sessions:  {session_weekly:>10,.0f} tokens saved")
print(f"  WEEKLY TOTAL:   {wt:>10,.0f} tokens saved")

mt = wt * 4.3
print()
print("MONTHLY PROJECTION (4.3 weeks):")
print("-" * 60)
print(f"  MONTHLY TOTAL:  {mt:>10,.0f} tokens saved")
print(f"  Opus ($15/MTok):   ${mt * 15 / 1e6:.2f}/month saved")
print(f"  Sonnet ($3/MTok):  ${mt * 3 / 1e6:.2f}/month saved")

# Context window impact
print()
print("CONTEXT WINDOW IMPACT:")
print("-" * 60)
avg_without = 15_000
avg_with = int(tpd / max(ppd, 1))
print(f"  Per message WITHOUT tool: ~{avg_without:,} tokens")
print(f"  Per message WITH tool:    ~{avg_with:,} tokens")
print(f"  Reduction: {(1 - avg_with / avg_without) * 100:.0f}%")
print()
cw = 200_000
mw = cw // max(avg_with, 1)
mwo = cw // avg_without
print(f"  In 200K context window:")
print(f"    WITHOUT tool: ~{mwo} messages before context full")
print(f"    WITH tool:    ~{mw} messages before context full")
print(f"    You get {mw // max(mwo, 1)}x MORE messages per conversation")

print()
print("OPUS RATE LIMIT IMPACT:")
print("-" * 60)
print(f"  Opus: ~45 messages / 5 hours")
t_without = 45 * avg_without
t_with = 45 * avg_with
print(f"  45 msgs WITHOUT tool: {t_without:,} input tokens consumed")
print(f"  45 msgs WITH tool:    {t_with:,} input tokens consumed")
print(f"  SAVED per limit cycle: {t_without - t_with:,} tokens ({(1 - t_with / t_without) * 100:.0f}%)")
print(f"  = more room for Claude's responses and reasoning")

# Scaling projections
print()
print("SCALING PROJECTIONS:")
print("-" * 60)
aspp = total_saved / max(total_prompts, 1)
for label, rate in [("Current", ppd), ("Moderate (20/day)", 20),
                    ("Heavy (35/day)", 35), ("Power user (50/day)", 50)]:
    w = rate * 5 * aspp + session_weekly
    m = w * 4.3
    print(f"  {label:25s}: {m:>12,.0f} tok/month"
          f" = ${m * 3 / 1e6:.2f} Sonnet / ${m * 15 / 1e6:.2f} Opus")

print()
print("=" * 60)
print("BOTTOM LINE")
print("=" * 60)
print(f"  Current rate: {ppd:.0f} prompts/day, {aspp:,.0f} tokens saved/prompt")
print(f"  Weekly:  {wt:,.0f} tokens saved")
print(f"  Monthly: {mt:,.0f} tokens saved (${mt * 15 / 1e6:.2f} Opus)")
print(f"  You get {mw // max(mwo, 1)}x more messages per conversation")
print(f"  Every prompt is {(1 - avg_with / avg_without) * 100:.0f}% lighter")

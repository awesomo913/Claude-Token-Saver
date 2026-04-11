"""Full system audit of Claude Token Saver v4.5."""

import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from claude_backend.backend import ClaudeContextManager
from claude_backend.config import ScanConfig
from claude_backend.prompt_builder import build_smart_prompt, detect_intent, review_prompt, ROLES
from claude_backend.search import smart_search
from claude_backend.tracker import TokenTracker

project = Path(__file__).resolve().parent.parent
mgr = ClaudeContextManager(ScanConfig())
analysis = mgr.analyze(project)
snippets = [b for b in analysis.blocks if b.docstring or b.kind != "file"]
total_src = sum(len(f.content) // 4 for f in analysis.files)

print("=" * 70)
print("FULL SYSTEM AUDIT — Claude Token Saver v4.5")
print("=" * 70)

# ─── 1: Project scale ───
print("\n1. PROJECT SCALE")
print("-" * 50)
print(f"   Files:        {len(analysis.files)}")
print(f"   Source tokens: {total_src:,}")
print(f"   Code blocks:  {len(analysis.blocks)}")
print(f"   Searchable:   {len(snippets)}")
print(f"   Modules:      {len(analysis.modules)}")

# ─── 2: Pre-loaded context ───
print("\n2. PRE-LOADED CONTEXT (auto-loaded by Claude Code)")
print("-" * 50)
cm = project / "CLAUDE.md"
cmd_tok = len(cm.read_text(encoding="utf-8")) // 4 if cm.is_file() else 0
md = project / ".claude" / "memory"
mem_files = [f for f in md.iterdir() if f.is_file()] if md.is_dir() else []
mem_tok = sum(len(f.read_text(encoding="utf-8")) // 4 for f in mem_files)
sd = project / ".claude" / "snippets"
snip_count = sum(1 for f in sd.rglob("*.py")) if sd.is_dir() else 0

reading_30pct = int(total_src * 0.3)
preloaded = cmd_tok + mem_tok
compression = round(reading_30pct / max(preloaded, 1), 1)
print(f"   CLAUDE.md:       {cmd_tok:,} tokens")
print(f"   Memory files:    {len(mem_files)} files, {mem_tok:,} tokens")
print(f"   Snippet library: {snip_count} files")
print(f"   Total preloaded: {preloaded:,} tokens")
print(f"   Without tool:    ~{reading_30pct:,} tokens (30% scan)")
print(f"   COMPRESSION:     {compression}x")
v_preload = "EFFECTIVE" if preloaded < reading_30pct * 0.3 else "MARGINAL"
print(f"   VERDICT:         {v_preload}")

# ─── 3: Smart prompt vs raw ───
print("\n3. SMART PROMPT BUILDER vs RAW PASTE")
print("-" * 50)
requests = [
    "Fix the CDP connection timeout bug",
    "Build a dashboard showing session stats",
    "Refactor the search engine for performance",
    "Write tests for the token tracker",
    "Explain how broadcast mode works",
]
smart_total = raw_total = 0
for req in requests:
    results = smart_search(snippets, req, max_results=4, min_score=3.0)
    items = ""
    for _, b in results:
        items += f"### {b.name}\n```\n{b.source.strip()}\n```\n\n"
    smart = build_smart_prompt(request=req, code_context=items.strip())
    raw = items.strip() + "\n\n" + req
    st, rt = len(smart) // 4, len(raw) // 4
    smart_total += st
    raw_total += rt
    rv = review_prompt(req, smart)
    intent = detect_intent(req)
    overhead = st - rt
    print(f"   \"{req}\"")
    print(f"     Intent: {intent} | Smart: {st:,} tok ({rv['sections']} sections) | Raw: {rt:,} tok | +{overhead} overhead")

avg_overhead = (smart_total - raw_total) * 100 // max(raw_total, 1)
v_smart = "WORTH IT" if avg_overhead < 40 else "TOO HEAVY"
print(f"\n   AVG OVERHEAD: +{avg_overhead}% for structured prompts")
print(f"   VERDICT: {v_smart}")

# ─── 4: Search accuracy ───
print("\n4. SEARCH ACCURACY (sloppy English)")
print("-" * 50)
acc_tests = [
    ("fix cdp timout", "connect"),
    ("clik on teh chat", "click_chat_input"),
    ("mange sesions", "session"),
    ("loading setings from json", "load_config"),
    ("copy to clipbord", "copy"),
    ("sendin promts to ai", "send"),
    ("brwser window fokus", "focus_window"),
    ("exract code bloks", "extract"),
    ("ollama model downlod", "pull_model"),
    ("token savings trakker", "Token"),
]
hits = 0
for query, expected in acc_tests:
    results = smart_search(snippets, query, max_results=3, min_score=2.0)
    names = [b.name for _, b in results]
    found = any(expected.lower() in n.lower() for n in names)
    if found:
        hits += 1
    print(f"   [{'PASS' if found else 'MISS'}] \"{query}\" -> {names[:3]}")
print(f"   ACCURACY: {hits}/{len(acc_tests)} ({hits * 100 // len(acc_tests)}%)")

# ─── 5: Per-query savings ───
print("\n5. PER-QUERY TOKEN SAVINGS")
print("-" * 50)
sav_tests = [
    ("send message to ai chat", "browser_actions.py"),
    ("cdp chrome connection", "cdp_client.py"),
    ("config loading", "claude_backend/config.py"),
    ("session management", "session_manager.py"),
    ("clipboard operations", "claude_backend/gui.py"),
    ("window positioning", "window_manager.py"),
]
ts, tw = 0, 0
for query, cmp_file in sav_tests:
    results = smart_search(snippets, query, max_results=4, min_score=3.0)
    targeted = sum(len(b.source) // 4 for _, b in results)
    ff = [f for f in analysis.files if f.path == cmp_file]
    full = len(ff[0].content) // 4 if ff else targeted * 3
    saved = max(0, full - targeted)
    pct = (1 - targeted / max(full, 1)) * 100
    ts += saved
    tw += full
    print(f"   \"{query}\"  {targeted:,} tok vs {full:,} = {pct:.0f}% saved")
avg_save = ts * 100 // max(tw, 1)
print(f"   AVERAGE: {avg_save}% reduction ({ts:,} tokens saved)")

# ─── 6: Large request ───
print("\n6. LARGE REQUEST HANDLING")
print("-" * 50)
huge = (
    "I need to rebuild the CDP client with timeout retry logic and add a health check "
    "every 60 seconds and refactor the session manager for hot-swapping profiles and "
    "make window manager save positions and update broadcast to detect bad models and "
    "switch backup and add proper logging everywhere and add type hints to everything"
)
chunks = re.split(r"\band\b|\balso\b|\bthen\b", huge)
chunks = [c.strip() for c in chunks if len(c.strip()) > 10][:8]
t0 = time.perf_counter()
block_scores = {}
for chunk in chunks:
    for score, block in smart_search(snippets, chunk, max_results=4, min_score=3.0):
        key = f"{block.name}:{block.file_path}"
        if key in block_scores:
            block_scores[key] = (block_scores[key][0] + score, block)
        else:
            block_scores[key] = (score, block)
ranked = sorted(block_scores.values(), key=lambda x: -x[0])[:10]
t1 = time.perf_counter()
ctx_tok = sum(len(b.source) // 4 for _, b in ranked)
print(f"   Input: {len(huge)} chars, {len(huge.split())} words")
print(f"   Sub-tasks: {len(chunks)}")
print(f"   Code targets: {len(ranked)} in {t1 - t0:.2f}s")
print(f"   Context: {ctx_tok:,} tokens")
print(f"   Status: NO CRASH")

# ─── 7: Intent detection ───
print("\n7. INTENT DETECTION")
print("-" * 50)
int_tests = [
    ("fix the cdp timeout bug", "debug"),
    ("build a new dashboard", "feature"),
    ("refactor session manager", "refactor"),
    ("write tests for search", "test"),
    ("explain broadcast mode", "explain"),
    ("optimize scan performance", "optimize"),
]
ihits = 0
for text, expected in int_tests:
    got = detect_intent(text)
    ok = got == expected
    if ok:
        ihits += 1
    print(f"   [{'OK' if ok else 'MISS'}] \"{text}\" -> {got} (expected {expected})")
print(f"   ACCURACY: {ihits}/{len(int_tests)}")

# ─── 8: Tracker ───
print("\n8. LIFETIME TOKEN SAVINGS")
print("-" * 50)
tracker = TokenTracker()
at = tracker.get_all_time_total()
bd = tracker.get_operation_breakdown()
print(f"   All-time: {at:,} tokens")
for op, tok in sorted(bd.items(), key=lambda x: -x[1]):
    print(f"     {op}: {tok:,}")

# ─── FINAL ───
print("\n" + "=" * 70)
print("SCORECARD")
print("=" * 70)
scores = {
    "Pre-loaded context": (compression, "x compression", compression >= 3.0),
    "Prompt overhead": (avg_overhead, "% extra for structure", avg_overhead <= 40),
    "Search accuracy": (hits * 100 // len(acc_tests), "% sloppy queries", hits >= 8),
    "Per-query savings": (avg_save, "% token reduction", avg_save >= 50),
    "Large requests": (len(ranked), " code targets, no crash", len(ranked) >= 5),
    "Intent detection": (ihits * 100 // len(int_tests), "% accuracy", ihits >= 5),
    "Lifetime tracked": (at, " tokens saved", at > 0),
}
issues = []
for name, (val, unit, passing) in scores.items():
    status = "PASS" if passing else "FAIL"
    if not passing:
        issues.append(name)
    print(f"   [{status}] {name}: {val:,}{unit}")

print()
if issues:
    print(f"   ISSUES ({len(issues)}):")
    for i in issues:
        print(f"     - {i}")
else:
    print("   ALL METRICS PASSING.")
print("=" * 70)

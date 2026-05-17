# From: claude_backend/cli.py:377
# Print lifetime + recent token-savings ledger entries.

def _run_savings(project_filter: str = "", limit: int = 20) -> int:
    """Print lifetime + recent token-savings ledger entries."""
    from .tracker import TokenTracker

    tracker = TokenTracker()
    total = tracker.get_all_time_total()
    breakdown = tracker.get_operation_breakdown(project=project_filter)
    events = tracker.get_recent_events(limit=limit)
    if project_filter:
        events = [e for e in events if e.get("project") == project_filter]

    print("\n=== Token Saver savings ===\n")
    label = f"  Project: {project_filter}" if project_filter else "  All projects"
    print(label)
    if project_filter:
        proj_total = tracker.get_project_total(project_filter)
        print(f"  Lifetime tokens avoided: {proj_total}")
    else:
        print(f"  Lifetime tokens avoided: {total}")

    if breakdown:
        print("\n  By operation:")
        for op, n in sorted(breakdown.items(), key=lambda x: -x[1]):
            print(f"    {op:<16} {n}")

    if not events:
        print("\n  No events yet.")
        return 0

    print(f"\n  Recent events (last {len(events)}):")
    print(f"    {'time':<25}  {'op':<14}  {'avoided':>8}  project")
    for e in events:
        ts = e.get("ts", "")[:19]
        op = e.get("op", "")
        avoided = e.get("tokens_avoided", e.get("tokens", 0))
        proj = e.get("project", "")
        print(f"    {ts:<25}  {op:<14}  {avoided:>8}  {proj}")
    print()
    return 0

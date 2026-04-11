"""How much more you get from Claude Pro 20x Max using the Token Saver."""

print("CLAUDE PRO 20x MAX PLAN -- USAGE EXTENSION ANALYSIS")
print("=" * 65)

avg_without = 15000   # measured: avg input tokens per msg, no tool
avg_with = 8645       # measured: your actual rate with tool
avg_response = 5000   # Claude avg response size
cw = 200_000          # context window

exchange_without = avg_without + avg_response   # 20K per round trip
exchange_with = avg_with + avg_response         # 13.6K per round trip

turns_without = cw // exchange_without
turns_with = cw // exchange_with
extra_turns = turns_with - turns_without

print()
print("CONVERSATION LENGTH (before context fills up)")
print("-" * 65)
print(f"  WITHOUT tool: {turns_without} exchanges per conversation")
print(f"  WITH tool:    {turns_with} exchanges per conversation")
print(f"  EXTRA:        +{extra_turns} exchanges ({extra_turns * 100 // turns_without}% longer)")

print()
print("OPUS RATE LIMIT (45 msgs / 5 hours)")
print("-" * 65)
input_wo = 45 * avg_without
input_w = 45 * avg_with
freed = input_wo - input_w
print(f"  45 msgs WITHOUT: {input_wo:,} input tokens")
print(f"  45 msgs WITH:    {input_w:,} input tokens")
print(f"  Freed:           {freed:,} tokens ({freed * 100 // input_wo}%)")
print(f"  = {freed // avg_response} more detailed Claude responses in same window")

print()
print("DAILY USAGE (realistic ~120 messages/day)")
print("-" * 65)
daily = 120
d_wo = daily * avg_without
d_w = daily * avg_with
d_saved = d_wo - d_w
extra_msgs = d_saved // avg_with
print(f"  Input WITHOUT: {d_wo:,} tokens/day")
print(f"  Input WITH:    {d_w:,} tokens/day")
print(f"  Freed:         {d_saved:,} tokens/day")
print(f"  = {extra_msgs} extra messages worth of headroom")
print(f"  Effective capacity: {daily} + {extra_msgs} = {daily + extra_msgs} msgs/day")
print(f"  Thats {extra_msgs * 100 // daily}% more effective usage")

print()
print("CONVERSATION RESTARTS")
print("-" * 65)
restarts_wo = daily // turns_without
restarts_w = daily // turns_with
fewer = restarts_wo - restarts_w
restart_cost = 5000  # tokens to re-explain context
print(f"  WITHOUT tool: ~{restarts_wo} restarts/day (context fills every {turns_without} msgs)")
print(f"  WITH tool:    ~{restarts_w} restarts/day (context fills every {turns_with} msgs)")
print(f"  {fewer} fewer restarts/day")
print(f"  Each restart costs ~{restart_cost:,} tokens to re-explain")
print(f"  Daily restart savings: {fewer * restart_cost:,} tokens")

print()
print("MONTHLY ON 20x MAX PLAN")
print("-" * 65)
days = 22
m_msgs = daily * days
m_saved = d_saved * days
m_restart = fewer * restart_cost * days
m_total = m_saved + m_restart
m_extra = m_saved // avg_with + fewer * days
print(f"  Monthly messages:    {m_msgs:,}")
print(f"  Input saved:         {m_saved:,} tokens")
print(f"  Restart saved:       {m_restart:,} tokens")
print(f"  TOTAL FREED:         {m_total:,} tokens")
print(f"  Extra capacity:      {m_extra:,} messages worth")

print()
print("WHAT 42% LIGHTER MESSAGES ACTUALLY MEANS")
print("-" * 65)
print(f"  1. LONGER CONVERSATIONS")
print(f"     {turns_with} exchanges vs {turns_without} = {extra_turns * 100 // turns_without}% more back-and-forth")
print(f"     before Claude starts forgetting your earlier instructions")
print()
print(f"  2. BETTER RESPONSES")
print(f"     42% less noise in context = Claude focuses on YOUR code")
print(f"     not 500 lines of irrelevant functions from the same file")
print()
print(f"  3. FEWER RESTARTS")
print(f"     {fewer} fewer conversation restarts per day")
print(f"     each restart loses all built-up context")
print()
print(f"  4. MORE ROOM FOR CLAUDE")
print(f"     {freed:,} tokens freed per 45-msg Opus cycle")
print(f"     = Claude can generate longer code blocks")
print(f"     = more detailed explanations")
print(f"     = better reasoning before answering")

print()
print("=" * 65)
print("BOTTOM LINE FOR YOUR 20x PRO PLAN")
print("=" * 65)
print(f"  You get {extra_turns * 100 // turns_without}% longer conversations")
print(f"  You get {extra_msgs * 100 // daily}% more effective daily messages")
print(f"  You save {m_total:,} tokens/month from the same plan")
print(f"  {fewer} fewer conversation restarts per day")
print(f"  Claude gives sharper answers (less noise in context)")
print()
print(f"  Same $200/month plan, {extra_msgs * 100 // daily}% more productive use.")
